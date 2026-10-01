![memorytree](assets/logo.png)

Git for AI memory. Claude Code and Codex share one memory across every machine and account: relevant memories are recalled on every prompt, new ones are captured after every turn, and git keeps the full history of how each idea evolved.

Status: in development. Read [DESIGN.md](DESIGN.md) for how it works and [ROADMAP.md](ROADMAP.md) for the plan.

## Install

Claude Code:

```
/plugin marketplace add leonardomenezes8500/memorytree
/plugin install memorytree@memorytree
/memorytree:setup
```

Codex:

```
codex plugin marketplace add leonardomenezes8500/memorytree
codex plugin add memorytree@memorytree
```

Then trust the hooks in `/hooks` and ask Codex to run the memorytree setup skill.

You need Python 3.11+ and git.
