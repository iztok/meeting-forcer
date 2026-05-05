import webbrowser
import objc
from Foundation import NSObject, NSMakeRect
from AppKit import (
    NSWindow, NSScreen, NSColor, NSView, NSButton, NSTextField,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSFont,
)

# Above screen saver level so it covers everything
_OVERLAY_LEVEL = 1000


class _ActionTarget(NSObject):
    """Minimal ObjC target so NSButton can call back into Python."""

    def init(self):
        self = objc.super(_ActionTarget, self).init()
        if self is None:
            return None
        self._fn = None
        return self

    @objc.python_method
    def bind(self, fn):
        self._fn = fn
        return self

    def fire_(self, sender):
        if self._fn:
            self._fn()


class OverlayManager:
    def __init__(self):
        self._windows = []
        self._targets = []  # Strong refs prevent GC of ObjC objects

    def show(self, title, url, on_snooze=None):
        self.dismiss()
        self._targets = []

        screens = NSScreen.screens()
        main = NSScreen.mainScreen()

        for screen in screens:
            frame = screen.frame()
            win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                frame,
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False,
            )
            win.setBackgroundColor_(NSColor.blackColor())
            win.setLevel_(_OVERLAY_LEVEL)
            win.setOpaque_(True)
            win.setCollectionBehavior_(1 << 3)  # CanJoinAllSpaces
            win.setIgnoresMouseEvents_(False)

            if screen == main:
                win.setContentView_(self._make_content(frame, title, url, on_snooze))

            win.makeKeyAndOrderFront_(None)
            self._windows.append(win)

    def _make_content(self, frame, title, url, on_snooze):
        W = frame.size.width
        H = frame.size.height
        cx, cy = W / 2, H / 2

        root = NSView.alloc().initWithFrame_(frame)

        def label(text, x, y, w, h, size, color, bold=False):
            f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
            f.setStringValue_(text)
            f.setBezeled_(False)
            f.setDrawsBackground_(False)
            f.setEditable_(False)
            f.setSelectable_(False)
            f.setTextColor_(color)
            f.setFont_(NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size))
            f.setAlignment_(2)  # NSTextAlignmentCenter
            root.addSubview_(f)

        white = NSColor.whiteColor()
        gray = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.65, 0.65, 0.65, 1.0)
        dim = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.4, 0.4, 0.4, 1.0)

        label("Meeting Time!", cx - 350, cy + 110, 700, 64, 48, white, bold=True)
        label(title, cx - 350, cy + 46, 700, 48, 22, gray)
        label("Join now to dismiss this screen.", cx - 350, cy + 4, 700, 36, 15, dim)

        # Join button
        join_btn = NSButton.alloc().initWithFrame_(NSMakeRect(cx - 130, cy - 80, 260, 54))
        join_btn.setTitle_("Join Meeting")
        join_btn.setBezelStyle_(1)  # NSBezelStyleRounded
        join_btn.setFont_(NSFont.boldSystemFontOfSize_(18))

        def on_join():
            webbrowser.open(url)
            self.dismiss()

        join_target = _ActionTarget.alloc().init().bind(on_join)
        self._targets.append(join_target)
        join_btn.setTarget_(join_target)
        join_btn.setAction_("fire:")
        root.addSubview_(join_btn)

        # Snooze button
        snooze_btn = NSButton.alloc().initWithFrame_(NSMakeRect(cx - 70, cy - 148, 140, 36))
        snooze_btn.setTitle_("Snooze 5 min")
        snooze_btn.setBezelStyle_(1)
        snooze_btn.setFont_(NSFont.systemFontOfSize_(13))

        def on_snooze_click():
            self.dismiss()
            if on_snooze:
                on_snooze()

        snooze_target = _ActionTarget.alloc().init().bind(on_snooze_click)
        self._targets.append(snooze_target)
        snooze_btn.setTarget_(snooze_target)
        snooze_btn.setAction_("fire:")
        root.addSubview_(snooze_btn)

        return root

    def dismiss(self):
        for win in self._windows:
            win.close()
        self._windows.clear()
        self._targets.clear()
