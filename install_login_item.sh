#!/bin/bash
# Installs a LaunchAgent so Meeting Forcer starts automatically on login.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.meetingforcer.app.plist"

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.meetingforcer.app</string>
  <key>ProgramArguments</key>
  <array>
    <string>$SCRIPT_DIR/.venv/bin/python</string>
    <string>$SCRIPT_DIR/app.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <!-- KeepAlive omitted on purpose: with KeepAlive=true, macOS instantly
       respawns the app when killed, making it impossible to stop. The app
       should only start at login, not be revived on crash/quit. -->
  <key>StandardOutPath</key>
  <string>$HOME/.meeting-forcer/meeting-forcer.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/.meeting-forcer/meeting-forcer.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "✅  Meeting Forcer will now start automatically on login."
echo "    To stop it:  launchctl unload $PLIST"
