"""
Manual meetings: stored as a list in ~/.meeting-forcer/manual_meetings.json.
Each entry: {"id": str, "title": str, "url": str, "time": "HH:MM", "days": [0-6]}
days: 0=Mon … 6=Sun. Empty list means every day.
"""
import json
import os
import datetime
import uuid

STORE_PATH = os.path.expanduser("~/.meeting-forcer/manual_meetings.json")


def _load():
    if not os.path.exists(STORE_PATH):
        return []
    with open(STORE_PATH) as f:
        return json.load(f)


def _save(meetings):
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(meetings, f, indent=2)


def all_meetings():
    return _load()


def add_meeting(title, url, time_str, days=None):
    meetings = _load()
    meetings.append({
        "id": str(uuid.uuid4()),
        "title": title,
        "url": url,
        "time": time_str,    # "HH:MM"
        "days": days or [],  # [] = every day
    })
    _save(meetings)


def remove_meeting(meeting_id):
    meetings = [m for m in _load() if m["id"] != meeting_id]
    _save(meetings)


def get_active_meetings(window_minutes=2):
    """Return manual meetings whose scheduled time is within ±window_minutes of now."""
    now = datetime.datetime.now()
    results = []
    for m in _load():
        try:
            h, mi = map(int, m["time"].split(":"))
        except ValueError:
            continue

        days = m.get("days", [])
        if days and now.weekday() not in days:
            continue

        meeting_time = now.replace(hour=h, minute=mi, second=0, microsecond=0)
        diff = (meeting_time - now).total_seconds()
        if -60 <= diff <= window_minutes * 60:
            results.append(m)
    return results
