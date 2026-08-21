#!/bin/sh
# Locate gate.py, then run it with whatever Python is on PATH.
# CLAUDE_PLUGIN_ROOT is set for plugin installs; skills.sh copies only the
# skill dir, so fall back to this script's parent.
set -eu
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/skills/prompt-comments/scripts/gate.py" ]; then
  GATE="$CLAUDE_PLUGIN_ROOT/skills/prompt-comments/scripts/gate.py"
else
  HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  if [ -f "$HERE/../skills/prompt-comments/scripts/gate.py" ]; then
    GATE="$HERE/../skills/prompt-comments/scripts/gate.py"
  elif [ -f "$HERE/../scripts/gate.py" ]; then
    GATE="$HERE/../scripts/gate.py"
  elif [ -f "$HOME/.agents/skills/prompt-comments/scripts/gate.py" ]; then
    GATE="$HOME/.agents/skills/prompt-comments/scripts/gate.py"
  else
    exit 0
  fi
fi
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  exit 0
fi
exec "$PY" "$GATE"
