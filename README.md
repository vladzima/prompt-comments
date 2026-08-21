# prompt-comments

Stops `AGENTS.md` / `CLAUDE.md` from growing without bound.

Adding an instruction is cheap. Deleting it is a guess once nobody remembers
why it exists. This package makes the *agent* write the why at add time, even
when the user never mentioned the file.

Based on Chakrabarti, [*Why Does CLAUDE.md Keep Growing?*](https://arxiv.org/abs/2608.11095)
(arXiv:2608.11095).

## How a user uses this

They install it. Then they keep working. They do not invoke a slash command
and they do not ask the agent to update instructions.

Agents already add rules to `AGENTS.md` / `CLAUDE.md` as a side effect of
normal work. After install:

1. **Skill description** tells the agent to load this protocol whenever *it*
   edits those files, not only when the user names them.
2. **Write-time hook** (Claude Code / Codex plugin) intercepts `Write`/`Edit`
   of those files and blocks new instructions that lack `failed` / `outcome` /
   `recurred` comments. Existing uncommented files stay editable.
3. **Prime extension** does the same on `edit` / `ipython` / `bash`.
4. **`AGENTS.md` fallback** for hosts that only inject a context file
   (Gemini CLI and others).

## Install

### skills.sh (70+ agents)

```sh
npx skills add vladzima/prompt-comments -g --all
```

That installs the skill. For write-time blocking in Claude Code, also:

```sh
claude plugin marketplace add vladzima/prompt-comments
claude plugin install prompt-comments@prompt-comments
```

### Prime Agent

```sh
prime-agent package install https://github.com/vladzima/prompt-comments
```

Loads the skill *and* the write-time extension.

### Manual

```sh
git clone https://github.com/vladzima/prompt-comments.git
```

Then copy `skills/prompt-comments` into your agent's skills dir.

## What the agent writes

```md
Use bun, not npm.
# failed: npm install rewrote the lockfile and broke CI (2026-03-12)
# try: bun matches CI
# outcome: lockfile stable after switch
# recurred: 2
```

No named failure → do not add the rule. No outcome → do not add the comment.
Deletes stay manual. Wholesale rewrites must port comments.

## Not included

No auto-pruner. The paper's warning: writing a comment is safe; acting on one
to delete is not. Keep a human in the deletion path.

## License

MIT.
