#!/usr/bin/env python3
"""Write-time gate for durable agent instruction files.

Reads a JSON hook payload on stdin (or a file path argv). If the write adds
instruction lines without failed/outcome/recurred comments, deny.

Existing uncommented files stay editable. Only *new* instruction lines are
gated. Any parse/IO error exits 0 so the host is never bricked.
"""
from __future__ import annotations

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

INSTRUCTION_BASENAMES = {
    "agents.md",
    "claude.md",
    "claude.local.md",
    "gemini.md",
    "copilot-instructions.md",
}

INSTRUCTION_PATH_PARTS = (
    "/.claude/rules/",
    "/.agents/rules/",
    "/.cursor/rules/",
    "/.windsurf/rules/",
    "/.clinerules/",
)

COMMENT_KEYS = ("failed", "outcome", "recurred")
KEY_RE = re.compile(
    r"^\s{0,3}#\s*(failed|outcome|recurred|try)\s*:",
    re.I,
)
MD_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
HTML_COMMENT_RE = re.compile(r"^\s*<!--")
FRONTMATTER_LINE_RE = re.compile(r"^---\s*$")
NUDGE = (
    "prompt-comments: new durable instructions need a write-time comment "
    "with failed, outcome, and recurred. Do not invent a why. Do not "
    "auto-delete. Safety/auth/data-loss rules stay until a human says "
    "otherwise. Example:\n"
    "Use bun, not npm.\n"
    "# failed: npm install rewrote the lockfile and broke CI (2026-03-12)\n"
    "# try: bun matches CI\n"
    "# outcome: lockfile stable after switch\n"
    "# recurred: 2"
)
REMINDER = (
    "prompt-comments: you are editing a durable instruction file. "
    "New instructions need failed/outcome/recurred comments. "
    "Do not auto-delete. Do not invent a why."
)
PATH_IN_CODE_RE = re.compile(
    r"""['"]([^'"]*(?:AGENTS|CLAUDE|GEMINI|copilot-instructions)[^'"]*)['"]""",
    re.I,
)
WRITE_TEXT_TRIPLE_RE = re.compile(
    r'write_text\(\s*(?:"""|\'\'\')([\s\S]*?)(?:"""|\'\'\')'
)
WRITE_TEXT_DOUBLE_RE = re.compile(r'write_text\(\s*"(.*?)"', re.S)
WRITE_TEXT_SINGLE_RE = re.compile(r"write_text\(\s*'(.*?)'", re.S)
NEW_STR_TRIPLE_RE = re.compile(
    r'new_str(?:ing)?\s*=\s*(?:"""|\'\'\')([\s\S]*?)(?:"""|\'\'\')'
)


def norm_path(path: str) -> str:
    return path.replace("\\", "/")


def is_instruction_file(path: str) -> bool:
    p = norm_path(path).lower()
    base = p.rsplit("/", 1)[-1]
    if base in INSTRUCTION_BASENAMES:
        return True
    return any(part in p for part in INSTRUCTION_PATH_PARTS)


def extract_tool(payload: dict) -> tuple[str, dict]:
    tool = (
        payload.get("tool_name")
        or payload.get("toolName")
        or payload.get("tool")
        or ""
    )
    inp = payload.get("tool_input") or payload.get("input") or payload
    if not isinstance(inp, dict):
        inp = {}
    return str(tool), inp


def extract_path(inp: dict) -> str:
    for key in ("file_path", "path", "filePath", "target_file"):
        val = inp.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


def extract_old_new(tool: str, inp: dict) -> tuple[str | None, str]:
    tool_l = tool.lower()
    new = ""
    old: str | None = None
    if tool_l in {"write", "create"}:
        for key in ("content", "contents"):
            val = inp.get(key)
            if isinstance(val, str):
                new = val
                break
        return old, new
    if tool_l in {"edit", "strreplace", "str_replace"}:
        for key in ("new_string", "new_str", "newString"):
            val = inp.get(key)
            if isinstance(val, str):
                new = val
                break
        for key in ("old_string", "old_str", "oldString"):
            val = inp.get(key)
            if isinstance(val, str):
                old = val
                break
        return old, new
    for key in ("content", "contents", "new_string", "new_str", "code"):
        val = inp.get(key)
        if isinstance(val, str) and val:
            new = val
            break
    return old, new


def is_comment_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if KEY_RE.match(line) or KEY_RE.match(s):
        return True
    if HTML_COMMENT_RE.match(s):
        return True
    if s.startswith("#") and not MD_HEADING_RE.match(line):
        return True
    return False


def attached_comment_keys(lines: list[str], start: int) -> set[str]:
    keys: set[str] = set()
    i = start
    while i < len(lines) and is_comment_line(lines[i]):
        m = KEY_RE.match(lines[i])
        if m:
            keys.add(m.group(1).lower())
        i += 1
    return keys


def is_instruction_line(line: str) -> bool:
    s = line.strip()
    if len(s) < 12:
        return False
    if is_comment_line(line):
        return False
    if MD_HEADING_RE.match(line):
        return False
    if s.startswith("```") or s.startswith("~~~"):
        return False
    if s.startswith("|") or s.startswith(">"):
        return False
    return True


def iter_instructions(text: str) -> list[tuple[str, set[str]]]:
    lines = text.splitlines()
    out: list[tuple[str, set[str]]] = []
    in_frontmatter = False
    in_fence = False
    i = 0
    if lines and FRONTMATTER_LINE_RE.match(lines[0]):
        in_frontmatter = True
        i = 1
    while i < len(lines):
        line = lines[i]
        if in_frontmatter:
            if FRONTMATTER_LINE_RE.match(line):
                in_frontmatter = False
            i += 1
            continue
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        if is_instruction_line(line):
            keys = attached_comment_keys(lines, i + 1)
            out.append((stripped, keys))
            i += 1
            while i < len(lines) and is_comment_line(lines[i]):
                i += 1
            continue
        i += 1
    return out


def similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= 0.8


def new_uncommented(old_text: str | None, new_text: str) -> list[str]:
    old_lines = [t for t, _ in iter_instructions(old_text or "")]
    missing: list[str] = []
    for text, keys in iter_instructions(new_text):
        if all(k in keys for k in COMMENT_KEYS):
            continue
        if any(text == o or similar(text, o) for o in old_lines):
            continue
        missing.append(text[:120])
    return missing


def read_existing(path: str) -> str | None:
    try:
        p = Path(path)
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return None


def extract_written_strings(code: str) -> list[str]:
    bodies: list[str] = []
    for rx in (
        WRITE_TEXT_TRIPLE_RE,
        WRITE_TEXT_DOUBLE_RE,
        WRITE_TEXT_SINGLE_RE,
        NEW_STR_TRIPLE_RE,
    ):
        bodies.extend(m.group(1) for m in rx.finditer(code))
    return bodies


def code_targets_instruction_file(code: str) -> bool:
    lower = code.lower()
    if any(name in lower for name in INSTRUCTION_BASENAMES):
        return True
    return any(part in norm_path(lower) for part in INSTRUCTION_PATH_PARTS)


def looks_like_shell_write(command: str) -> list[str]:
    cmd = command.strip()
    paths: list[str] = []
    for m in re.finditer(
        r"(?:^|[;&|]\s*)(?:cat|tee|cp|mv|install)\b[^\n]*?(?:>>?)\s*([^\s;|&]+)",
        cmd,
    ):
        paths.append(m.group(1).strip("\"'"))
    for m in re.finditer(
        r"(?:^|[;&|]\s*)(?:tee|cp|mv|install)\s+[^\n]*?(\S+\.(?:md|mdc))\b",
        cmd,
        re.I,
    ):
        paths.append(m.group(1).strip("\"'"))
    return [p for p in paths if is_instruction_file(p)]


def deny(message: str) -> int:
    sys.stdout.write(
        json.dumps(
            {
                "decision": "block",
                "reason": message,
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                    "additionalContext": message,
                },
            }
        )
        + "\n"
    )
    sys.stderr.write(message + "\n")
    return 2


def allow(extra: str | None = None) -> int:
    if extra:
        sys.stdout.write(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "additionalContext": extra,
                    }
                }
            )
            + "\n"
        )
    return 0


def gate_text(old_text: str | None, new_text: str) -> int:
    missing = new_uncommented(old_text, new_text)
    if missing:
        preview = "; ".join(missing[:3])
        return deny(f"{NUDGE}\nUncommented new instruction(s): {preview}")
    return allow(REMINDER)


def main() -> int:
    try:
        if len(sys.argv) > 1:
            raw = Path(sys.argv[1]).read_text(encoding="utf-8")
        else:
            raw = sys.stdin.read()
        if not raw.strip():
            return allow()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return allow()
        tool, inp = extract_tool(payload)
        path = extract_path(inp)
        tool_l = tool.lower()

        if tool_l in {"bash", "powershell", "shell"}:
            command = str(inp.get("command") or "")
            if looks_like_shell_write(command):
                return deny(
                    "prompt-comments: do not write instruction files through "
                    "the shell. Use the file-edit tool so write-time comments "
                    "can be checked.\n"
                    + NUDGE
                )
            return allow()

        if tool_l in {"ipython", "python"}:
            code = str(inp.get("code") or "")
            if not code_targets_instruction_file(code):
                return allow()
            bodies = extract_written_strings(code)
            if not bodies:
                return allow(REMINDER)
            old = None
            m = PATH_IN_CODE_RE.search(code)
            if m:
                old = read_existing(m.group(1))
            for body in bodies:
                rc = gate_text(old, body)
                if rc != 0:
                    return rc
            return allow(REMINDER)

        if not path or not is_instruction_file(path):
            return allow()

        snippet_old, new_text = extract_old_new(tool, inp)
        if not new_text:
            return allow(REMINDER)

        disk_old = read_existing(path)
        if tool_l in {"edit", "strreplace", "str_replace"}:
            old_text = snippet_old if snippet_old is not None else disk_old
        else:
            old_text = disk_old
        return gate_text(old_text, new_text)
    except Exception:
        return allow()


if __name__ == "__main__":
    raise SystemExit(main())
