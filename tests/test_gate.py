#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "skills" / "prompt-comments" / "scripts" / "gate.py"
PY = sys.executable

COMMENTED = """Use bun, not npm.
# failed: npm install rewrote the lockfile and broke CI (2026-03-12)
# try: bun matches CI
# outcome: lockfile stable after switch
# recurred: 2
"""

UNCOMMENTED = "Always use bun instead of npm for installs.\n"


def run(payload: dict) -> tuple[int, str, str]:
    proc = subprocess.run(
        [PY, str(GATE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def claude_write(path: str, content: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": path, "content": content},
    }


def claude_edit(path: str, old: str, new: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": path,
            "old_string": old,
            "new_string": new,
        },
    }


def test_empty_stdin_allows():
    proc = subprocess.run([PY, str(GATE)], input="", text=True, capture_output=True)
    assert proc.returncode == 0, proc.stderr


def test_readme_write_allows():
    code, _, err = run(claude_write("/tmp/README.md", UNCOMMENTED))
    assert code == 0, err


def test_agents_uncommented_denies():
    code, out, err = run(claude_write("/tmp/AGENTS.md", UNCOMMENTED))
    assert code == 2, (code, out, err)
    assert "failed" in err.lower()
    data = json.loads(out)
    assert data["permissionDecision"] == "deny"


def test_agents_commented_allows():
    code, out, err = run(claude_write("/tmp/AGENTS.md", COMMENTED))
    assert code == 0, err
    data = json.loads(out)
    assert "prompt-comments" in data["hookSpecificOutput"]["additionalContext"]


def test_existing_uncommented_edit_allows():
    payload = claude_edit(
        "/tmp/CLAUDE.md",
        "Always use bun instead of npm for installs.",
        "Always use bun instead of npm for installs.",
    )
    code, _, err = run(payload)
    assert code == 0, err


def test_edit_adding_uncommented_denies():
    payload = claude_edit(
        "/tmp/CLAUDE.md",
        "Always use bun instead of npm for installs.",
        "Always use bun instead of npm for installs.\nNever run migrations without asking first.\n",
    )
    code, _, err = run(payload)
    assert code == 2, err


def test_edit_adding_commented_allows():
    payload = claude_edit(
        "/tmp/CLAUDE.md",
        "Always use bun instead of npm for installs.",
        "Always use bun instead of npm for installs.\n" + COMMENTED,
    )
    code, _, err = run(payload)
    assert code == 0, err


def test_heading_and_short_lines_ignored():
    content = "# Project\n\nUse bun.\n"
    code, _, err = run(claude_write("/tmp/AGENTS.md", content))
    assert code == 0, err


def test_code_fence_ignored():
    content = "```\nAlways use bun instead of npm for installs.\n```\n"
    code, _, err = run(claude_write("/tmp/GEMINI.md", content))
    assert code == 0, err


def test_bash_redirect_denies():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "cat > AGENTS.md <<'EOF'\nhi\nEOF"},
    }
    code, _, err = run(payload)
    assert code == 2, err


def test_bash_unrelated_allows():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"},
    }
    code, _, err = run(payload)
    assert code == 0, err


def test_ipython_uncommented_denies():
    payload = {
        "tool": "ipython",
        "input": {
            "code": 'from pathlib import Path\nPath("AGENTS.md").write_text("""Always use bun instead of npm for installs.\\n""")\n'
        },
    }
    code, _, err = run(payload)
    assert code == 2, err


def test_ipython_unrelated_allows():
    payload = {
        "tool": "ipython",
        "input": {"code": "print(1+1)"},
    }
    code, _, err = run(payload)
    assert code == 0, err


def test_garbage_json_allows():
    proc = subprocess.run(
        [PY, str(GATE)], input="not json", text=True, capture_output=True
    )
    assert proc.returncode == 0


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok", name)
            except AssertionError as e:
                failed += 1
                print("FAIL", name, e)
    sys.exit(1 if failed else 0)
