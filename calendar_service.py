import os
import re
import datetime

CONFIG_DIR = os.path.expanduser("~/.meeting-forcer")
TOKEN_PATH = os.path.join(CONFIG_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, "credentials.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

MEET_PATTERN = re.compile(r"https://meet\.google\.com/[a-z][-a-z0-9]{2,}-[a-z][-a-z0-9]{2,}-[a-z][-a-z0-9]{2,}")
ZOOM_PATTERN = re.compile(r"https://[a-z0-9.]*zoom\.us/j/[^\s<>\"&]+")
TEAMS_PATTERN = re.compile(r"https://teams(?:\.live)?\.microsoft\.com/l/meetup-join/[^\s<>\"&]+")
WEBEX_PATTERN = re.compile(r"https://[a-z0-9]+\.webex\.com/[^\s<>\"&]+")


def _extract_url(event):
    # Google Meet via conferenceData
    for ep in event.get("conferenceData", {}).get("entryPoints", []):
        if ep.get("entryPointType") == "video":
            return ep.get("uri")

    text = " ".join([
        event.get("description") or "",
        event.get("location") or "",
        event.get("hangoutLink") or "",
    ])

    for pattern in (MEET_PATTERN, ZOOM_PATTERN, TEAMS_PATTERN, WEBEX_PATTERN):
        m = pattern.search(text)
        if m:
            return m.group(0).rstrip(".,;)")

    return None


class CalendarService:
    def __init__(self):
        self._service = None
        self._try_authenticate()

    def _try_authenticate(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            if os.path.exists(TOKEN_PATH):
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(CREDENTIALS_PATH):
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    return  # Not configured yet

                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())

            self._service = build("calendar", "v3", credentials=creds)
        except Exception as e:
            print(f"[calendar] auth failed: {e}")

    def is_ready(self):
        return self._service is not None

    def get_meetings_in_window(self, minutes_before: int, minutes_after: int = 5):
        """Return meetings that start within [now-minutes_after, now+minutes_before]."""
        if not self._service:
            return []
        try:
            now = datetime.datetime.utcnow()
            time_min = (now - datetime.timedelta(minutes=minutes_after)).isoformat() + "Z"
            time_max = (now + datetime.timedelta(minutes=minutes_before)).isoformat() + "Z"

            result = self._service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            meetings = []
            for ev in result.get("items", []):
                url = _extract_url(ev)
                if url:
                    meetings.append({
                        "id": ev["id"],
                        "title": ev.get("summary") or "Meeting",
                        "url": url,
                    })
            return meetings
        except Exception as e:
            print(f"[calendar] fetch failed: {e}")
            return []
