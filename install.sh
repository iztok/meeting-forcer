#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

echo "==> Creating virtual environment…"
python3 -m venv "$VENV"

echo "==> Installing dependencies…"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"

echo "==> Creating config directory…"
mkdir -p ~/.meeting-forcer

echo "==> Creating launcher…"
cat > "$SCRIPT_DIR/run.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/app.py"
EOF
chmod +x "$SCRIPT_DIR/run.sh"

echo ""
echo "✅  Done! Start with:  ./run.sh"
echo ""
echo "To auto-start on login, run:  ./install_login_item.sh"
