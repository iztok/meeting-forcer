import datetime
import webbrowser
import objc
from Foundation import NSObject, NSMakeRect, NSMakeSize, NSMakePoint
from AppKit import (
    NSWindow, NSScreen, NSColor, NSView, NSButton, NSTextField, NSBox,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSFont, NSAttributedString,
    NSForegroundColorAttributeName, NSFontAttributeName,
    NSParagraphStyleAttributeName, NSMutableParagraphStyle,
    NSKernAttributeName,
)

_OVERLAY_LEVEL = 1000
_NSBoxCustom = 4
_NSNoTitle = 0
_LEFT = 0
_CENTER = 2

# Palette
_BLACK  = lambda: NSColor.blackColor()
_WHITE  = lambda: NSColor.whiteColor()
_YELLOW = lambda: NSColor.colorWithCalibratedRed_green_blue_alpha_(0.97, 0.93, 0.0, 1.0)
_DIM    = lambda: NSColor.colorWithCalibratedRed_green_blue_alpha_(0.35, 0.35, 0.35, 1.0)

# Mono font shorthand
def _mono(size, weight=1.0):
    return NSFont.monospacedSystemFontOfSize_weight_(size, weight)


def _field(text, x, y, w, h, font, color, align=_LEFT):
    f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    f.setStringValue_(text)
    f.setBezeled_(False)
    f.setDrawsBackground_(False)
    f.setEditable_(False)
    f.setSelectable_(False)
    f.setTextColor_(color)
    f.setFont_(font)
    f.setAlignment_(align)
    return f


def _rule(x, y, w, h):
    """Solid white horizontal rule via NSBox (no Quartz CGColor needed)."""
    box = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    box.setBoxType_(4)       # NSBoxCustom
    box.setFillColor_(_WHITE())
    box.setBorderColor_(_WHITE())
    box.setBorderWidth_(0)
    box.setCornerRadius_(0)
    box.setTitlePosition_(0) # NSNoTitle
    return box


class _ActionTarget(NSObject):
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
        self._targets = []

    def show(self, title, url):
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
            win.setBackgroundColor_(_BLACK())
            win.setLevel_(_OVERLAY_LEVEL)
            win.setOpaque_(True)
            win.setCollectionBehavior_(1 << 3)  # CanJoinAllSpaces
            win.setIgnoresMouseEvents_(False)

            if screen == main:
                win.setContentView_(self._make_content(frame, title, url))

            win.makeKeyAndOrderFront_(None)
            self._windows.append(win)

    def _make_content(self, frame, title, url):
        W = frame.size.width
        H = frame.size.height

        # Grid: left margin = 10% of width, content width = 80%
        ML = W * 0.10
        CW = W * 0.80

        # Vertical anchor: build upward from ~40% height
        BASE_Y = H * 0.38

        root = NSView.alloc().initWithFrame_(frame)

        # ── top metadata row ───────────────────────────────────────────────
        now_str = datetime.datetime.now().strftime("%H:%M")
        root.addSubview_(_field(
            "MEETING IN PROGRESS",
            ML, H * 0.88, CW * 0.6, 22,
            _mono(11, 0.0), _DIM(), _LEFT,
        ))
        root.addSubview_(_field(
            now_str,
            ML, H * 0.88, CW, 22,
            _mono(11, 0.0), _DIM(), _CENTER,
        ))

        # ── thick top rule ─────────────────────────────────────────────────
        root.addSubview_(_rule(ML, H * 0.84, CW, 3))

        # ── meeting title ─────────────────────────────────────────────────
        # Clamp font size so long titles don't overflow
        title_size = max(36.0, min(80.0, 1800.0 / max(len(title), 1)))
        title_h = title_size * 2.2
        title_y = BASE_Y + 90

        root.addSubview_(_field(
            title.upper(),
            ML, title_y, CW, title_h,
            _mono(title_size, 1.0), _WHITE(), _LEFT,
        ))

        # ── thin rule below title ─────────────────────────────────────────
        root.addSubview_(_rule(ML, BASE_Y + 72, CW, 2))

        # ── helper copy ──────────────────────────────────────────────────
        root.addSubview_(_field(
            "YOU ARE LATE. CLICK THE BUTTON.",
            ML, BASE_Y + 36, CW, 26,
            _mono(12, 0.0), _DIM(), _LEFT,
        ))

        # ── JOIN button ───────────────────────────────────────────────────
        BTN_W, BTN_H = min(CW, 520.0), 72.0
        BTN_X = ML
        BTN_Y = BASE_Y - 32

        # Yellow box (visual background)
        box = NSBox.alloc().initWithFrame_(NSMakeRect(BTN_X, BTN_Y, BTN_W, BTN_H))
        box.setBoxType_(_NSBoxCustom)
        box.setFillColor_(_YELLOW())
        box.setBorderColor_(_YELLOW())
        box.setBorderWidth_(0)
        box.setCornerRadius_(0)
        box.setTitlePosition_(_NSNoTitle)

        # Label inside the box
        cv = box.contentView()
        cv_w = cv.frame().size.width
        cv_h = cv.frame().size.height
        btn_label = _field(
            "JOIN NOW  →",
            0, 0, cv_w, cv_h,
            _mono(22, 1.0), _BLACK(), _CENTER,
        )
        cv.addSubview_(btn_label)
        root.addSubview_(box)

        # Transparent click target on top
        click = NSButton.alloc().initWithFrame_(NSMakeRect(BTN_X, BTN_Y, BTN_W, BTN_H))
        click.setBordered_(False)
        click.setTitle_("")
        click.setTransparent_(True)

        def on_join():
            webbrowser.open(url)
            self.dismiss()

        t = _ActionTarget.alloc().init().bind(on_join)
        self._targets.append(t)
        click.setTarget_(t)
        click.setAction_("fire:")
        root.addSubview_(click)

        return root

    def dismiss(self):
        for win in self._windows:
            win.close()
        self._windows.clear()
        self._targets.clear()
