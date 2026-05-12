#!/bin/bash
# Removes the Meeting Forcer LaunchAgent and stops any running instance.
PLIST="$HOME/Library/LaunchAgents/com.meetingforcer.app.plist"

launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
pkill -f "python.*meeting-forcer.*app.py" 2>/dev/null || true
rm -f "$HOME/.meeting-forcer/app.pid"

echo "✅  Meeting Forcer auto-start removed and any running instance stopped."
