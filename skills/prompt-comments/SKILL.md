---
name: prompt-comments
description: >
  You MUST use this skill whenever you add, edit, delete, rewrite, or review
  durable agent instructions — including AGENTS.md, CLAUDE.md, GEMINI.md,
  copilot-instructions.md, SKILL.md, prompt notes, and other inherited agent
  rules. Load it even if the user did not mention those files. Agents add
  these rules as a side effect; the user will not ask. Also use when
  instruction files keep growing, get wholesale-rewritten, or when the user
  mentions prompt comments, catastrophic remembering, or pruning agent
  context.
license: MIT
metadata:
  author: Vlad Arbatov
  version: "0.2.0"
  paper: "arXiv:2608.11095"
---

# Prompt comments

Agent instruction files grow because adding a rule is cheap and deleting it
is a guess once the *why* is gone. Write the why at add time. Do not
auto-delete from it.

This is write-time protocol. It applies whenever *you* change a durable
instruction file. The user will not ask. Do not wait for them to mention
AGENTS.md / CLAUDE.md / SKILL.md.

Paper: Chakrabarti, *Why Does CLAUDE.md Keep Growing?* ([arXiv:2608.11095](https://arxiv.org/abs/2608.11095)).
Evidence: [references/paper.md](references/paper.md)

## Files this covers

Durable instructions the next agent will inherit: `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `copilot-instructions.md`, `SKILL.md`, prompt notes, always-on
agent rules, and harness prompt addendums.

Not: one-off chat directions. Not: ordinary code comments.

## Add

Do not add an instruction unless you can name a failure it prevents.

Every new instruction gets a comment on the next line, or it does not get
added:

```md
Use bun, not npm.
# failed: npm install rewrote the lockfile and broke CI (2026-03-12)
# try: bun matches CI
# outcome: lockfile stable after switch
# recurred: 2
```

Required: **failed**, **outcome**, **recurred**. Optional: **try**.

If this file is also the executor prompt, one line:

```md
Use bun, not npm.
# failed: lockfile rewrite in CI, 2026-03-12; outcome: bun stable; n=2
```

A story with no outcome is worse than no comment. Do not invent a why.

## Edit

Update the comment when the instruction changes. If you cannot recover the
why (git log, PR, existing comment), restore it before editing, or leave
the instruction alone.

## Delete

Writing a comment is safe. Deleting from one is not.

1. Recover the why.
2. If the failure can no longer happen, delete the instruction.
3. If the why is gone, do **not** delete. Ask the user.
4. Safety, auth, data-loss, and permissions rules stay until a human says
   otherwise.
5. Never auto-prune. Never empty a file because it looks messy.

## Rewrite

A wholesale rewrite resets size, not the process. Files refill within a
few commits. If you rewrite, port every comment. A clean uncommented file
will grow again.

## Do not

- Wait for the user to mention the instruction file.
- Put rationale in the instruction text (that is how files bloat).
- Add comment-shaped filler ("important", "always", "the user prefers").
- Treat age as proof a rule is stale, or as proof it is still true.
- Expect a stronger model to keep the file small. Stronger models add more.
