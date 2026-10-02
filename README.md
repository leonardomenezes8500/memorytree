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

Then trust the hooks in `/hooks` and run the setup skill (type `$` and pick it, or just ask Codex to set up memorytree).

The `memorytree` command for your terminal (`~/.local/bin` by default):

```
make install                # PREFIX=/usr/local to change
make uninstall
```

Setup checks the requirements (git, Python 3.11+) and walks you through the rest, asking before every change.
