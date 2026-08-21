# prompt-comments

Agent Skill that stops `AGENTS.md` / `CLAUDE.md` / skill files from growing
without bound.

Adding an instruction is cheap. Deleting it is a guess once nobody remembers
why it exists. This skill makes the agent write the *why* at add time, and
refuses to auto-delete from that why.

Based on Chakrabarti, [*Why Does CLAUDE.md Keep Growing?*](https://arxiv.org/abs/2608.11095)
(arXiv:2608.11095).

## Install

### skills.sh (Claude Code, Codex, Cursor, Windsurf, and 70+ others)

```sh
npx skills add vladzima/prompt-comments
```

Global, all agents:

```sh
npx skills add vladzima/prompt-comments -g --all
```

### Prime Agent

```sh
prime-agent package install https://github.com/vladzima/prompt-comments
```

Prime also loads `~/.agents/skills/`, so the skills.sh global install is
enough if that directory is already on its search path.

### Manual

```sh
git clone https://github.com/vladzima/prompt-comments.git
# then copy or symlink skills/prompt-comments into your agent's skills dir
```

## What it does

When the agent adds a durable instruction, it must attach a comment:

```md
Use bun, not npm.
# failed: npm install rewrote the lockfile and broke CI (2026-03-12)
# try: bun matches CI
# outcome: lockfile stable after switch
# recurred: 2
```

Required: the failure, the outcome, how often it recurred. No outcome → do
not add the comment (it makes pruning *worse*). No named failure → do not
add the instruction.

Deletes stay manual. Wholesale rewrites must port comments or the file
refills.

## Not included

No linter. No auto-pruner. No harness plugin. The paper's own warning:
writing a comment is safe; acting on one to delete is not.

## License

MIT.
