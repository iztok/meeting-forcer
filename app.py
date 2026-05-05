#!/usr/bin/env python3
import datetime
import os
import rumps
from overlay import OverlayManager
from calendar_service import CalendarService
import meetings_store

CONFIG_DIR = os.path.expanduser("~/.meeting-forcer")
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, "credentials.json")

# How many minutes before start to trigger the overlay
TRIGGER_MINUTES_BEFORE = 1


class MeetingForcerApp(rumps.App):
    def __init__(self):
        super().__init__("📅", quit_button="Quit")

        self.overlay = OverlayManager()
        self.calendar = CalendarService()

        # meeting_id -> datetime after which we can show it again (None = permanent dismiss)
        self._shown: dict = {}

        self._status_item = rumps.MenuItem("Waiting for meetings…")
        self._status_item.set_callback(None)

        self.menu = [
            self._status_item,
            None,
            rumps.MenuItem("Add Manual Meeting…", callback=self._add_manual_meeting),
            rumps.MenuItem("Manage Manual Meetings", callback=self._manage_meetings),
            None,
            rumps.MenuItem("Setup Google Calendar…", callback=self._setup_google),
            rumps.MenuItem("Check Now", callback=self._check_now),
        ]

        # Immediate first check
        self._do_check()

    # ------------------------------------------------------------------ timers

    @rumps.timer(60)
    def _tick(self, _):
        self._do_check()

    # ------------------------------------------------------------------ core

    def _do_check(self):
        now = datetime.datetime.now()
        meetings = self._collect_meetings()

        # Update status label
        if meetings:
            next_m = meetings[0]
            self._status_item.title = f"⚡ {next_m['title']}"
        else:
            self._status_item.title = "No upcoming meetings"

        for m in meetings:
            mid = m["id"]
            suppress_until = self._shown.get(mid)

            if suppress_until is None and mid in self._shown:
                # Permanently dismissed (joined)
                continue
            if suppress_until and now < suppress_until:
                continue

            self._shown[mid] = suppress_until  # Mark as in-flight

            def make_snooze(meeting_id):
                def snooze():
                    self._shown[meeting_id] = datetime.datetime.now() + datetime.timedelta(minutes=5)
                return snooze

            def make_join_dismiss(meeting_id):
                # Permanently suppress after joining
                def dismiss():
                    self._shown[meeting_id] = None
                return dismiss

            mid_copy = mid
            self.overlay.show(
                title=m["title"],
                url=m["url"],
                on_snooze=make_snooze(mid_copy),
            )
            # Register permanent dismiss on join is handled inside overlay via webbrowser.open;
            # we mark it permanent here so repeated ticks don't re-show.
            self._shown[mid_copy] = None

    def _collect_meetings(self):
        results = []
        seen_ids = set()

        # Google Calendar
        if self.calendar.is_ready():
            for m in self.calendar.get_meetings_in_window(minutes_before=TRIGGER_MINUTES_BEFORE):
                if m["id"] not in seen_ids:
                    results.append(m)
                    seen_ids.add(m["id"])

        # Manual meetings
        for m in meetings_store.get_active_meetings(window_minutes=TRIGGER_MINUTES_BEFORE):
            if m["id"] not in seen_ids:
                results.append(m)
                seen_ids.add(m["id"])

        return results

    # ------------------------------------------------------------------ menu actions

    def _check_now(self, _):
        self._do_check()

    def _add_manual_meeting(self, _):
        win = rumps.Window(
            title="Add Manual Meeting",
            message="Paste the meeting URL (Google Meet, Zoom, Teams…):",
            default_text="https://meet.google.com/xxx-xxx-xxx",
            ok="Next",
            cancel="Cancel",
            dimensions=(400, 24),
        )
        r = win.run()
        if not r.clicked:
            return
        url = r.text.strip()
        if not url.startswith("http"):
            rumps.alert("Invalid URL", "Please enter a valid meeting URL.")
            return

        win2 = rumps.Window(
            title="Add Manual Meeting",
            message="Meeting title:",
            default_text="Team standup",
            ok="Next",
            cancel="Cancel",
            dimensions=(400, 24),
        )
        r2 = win2.run()
        if not r2.clicked:
            return
        title = r2.text.strip() or "Meeting"

        win3 = rumps.Window(
            title="Add Manual Meeting",
            message="Start time (HH:MM in 24h, e.g. 14:30):",
            default_text=datetime.datetime.now().strftime("%H:%M"),
            ok="Add",
            cancel="Cancel",
            dimensions=(200, 24),
        )
        r3 = win3.run()
        if not r3.clicked:
            return
        time_str = r3.text.strip()
        try:
            h, m = map(int, time_str.split(":"))
            assert 0 <= h <= 23 and 0 <= m <= 59
        except Exception:
            rumps.alert("Invalid time", "Please use HH:MM format, e.g. 09:00")
            return

        meetings_store.add_meeting(title, url, time_str)
        rumps.alert("Done", f'"{title}" added at {time_str}.\n\nThe overlay will appear 1 minute before start.')

    def _manage_meetings(self, _):
        all_m = meetings_store.all_meetings()
        if not all_m:
            rumps.alert("Manual Meetings", "No manual meetings saved.")
            return
        lines = [f"{i+1}. {m['title']} @ {m['time']}" for i, m in enumerate(all_m)]
        win = rumps.Window(
            title="Remove Manual Meeting",
            message="Enter the number of the meeting to remove (or Cancel):\n\n" + "\n".join(lines),
            default_text="",
            ok="Remove",
            cancel="Cancel",
            dimensions=(200, 24),
        )
        r = win.run()
        if not r.clicked:
            return
        try:
            idx = int(r.text.strip()) - 1
            assert 0 <= idx < len(all_m)
        except Exception:
            rumps.alert("Invalid input", "Please enter a valid number.")
            return
        meetings_store.remove_meeting(all_m[idx]["id"])
        rumps.alert("Removed", f'"{all_m[idx]["title"]}" removed.')

    def _setup_google(self, _):
        rumps.alert(
            title="Setup Google Calendar",
            message=(
                "To connect Google Calendar:\n\n"
                "1. Go to console.cloud.google.com\n"
                "2. Create a project → Enable 'Google Calendar API'\n"
                "3. Create OAuth 2.0 credentials (Desktop app)\n"
                "4. Download the JSON file\n"
                "5. Save it as:\n"
                f"   {CREDENTIALS_PATH}\n\n"
                "6. Restart Meeting Forcer.\n\n"
                "The app will open a browser window to complete sign-in on first run."
            ),
        )


if __name__ == "__main__":
    MeetingForcerApp().run()
