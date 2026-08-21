# prompt-comments (always-on fallback)

When you add, edit, delete, or rewrite durable agent instructions
(AGENTS.md, CLAUDE.md, GEMINI.md, copilot-instructions.md, inherited
rules), do it even if the user did not mention those files.

- Do not add an instruction unless you can name a failure it prevents.
- Attach a write-time comment: failed, outcome, recurred. Optional: try.
- Do not invent a why. A story with no outcome is worse than no comment.
- Never auto-delete. If the why is gone, ask the user.
- Safety, auth, data-loss, and permissions rules stay until a human says so.
- Wholesale rewrites must port every comment.

```md
Use bun, not npm.
# failed: npm install rewrote the lockfile and broke CI (2026-03-12)
# try: bun matches CI
# outcome: lockfile stable after switch
# recurred: 2
```
