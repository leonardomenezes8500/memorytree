---
name: setup
description: Set up memorytree on this machine - vault, built-in memory off, commandments, migration of existing memories, pins. Use when the user asks to set up or install memorytree, when memorytree reports it has no vault or is not active, or on a new machine.
---

# memorytree setup

`MT` below means `python3 <this plugin's root>/bin/memorytree`. Run the steps in order; on a machine that is already set up, each step only confirms what is in place. Show the user what you are about to change outside the vault and wait for a yes. Read [DESIGN.md](../../DESIGN.md) only if a step is unclear.

0. **Requirements.** Check each one and stop at the first that fails, saying how to fix it:
   - `git --version`, plus `git config user.name` and `git config user.email`, because every memory is a commit;
   - `python3 -c 'import sys; assert sys.version_info >= (3, 11)'`. If Python is missing or too old, recommend installing it with uv (https://docs.astral.sh/uv/), or with the system package manager;
   - the agent's own CLI on PATH (`claude --version` or `codex --version`), since the background capture runs it with the cheap model;
   - for an existing vault on GitHub: access to the private repository (`git ls-remote <url>`).
1. **Vault.** If `~/.memorytree` exists, run `MT init` (idempotent) and move on. Otherwise ask whether the user already has a vault repository from another machine:
   - yes: `MT init --clone <url>`;
   - no: `MT init`, then offer to create a **private** remote and push (`gh repo create <name> --private --source ~/.memorytree --push`). The vault holds personal context: never make it public.
2. **Built-in memory off.** memorytree refuses to run alongside it.
   - Claude Code: set `"autoMemoryEnabled": false` in `~/.claude/settings.json`, merging the key into the existing JSON and keeping every other key.
   - Codex: set `memories = false` under `[features]` in `~/.codex/config.toml`. It is off by default; setting it explicitly protects against a future default change.
3. **Commandments.** Run `MT install`. It writes a marked block into `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` and keeps everything else in those files.
4. **Migrate.** Offer to import what the agents already remember on this machine:
   - Claude Code: `~/.claude/projects/*/memory/*.md` (skip `MEMORY.md`, which is only an index);
   - Codex: `~/.codex/memories/`.

   Rewrite each one in English as a vault memory: `user/profile.md` for stable facts about the user, `projects/<name>/<file>.md`, `env/<file>.md` or `topics/<file>.md`. Each file starts with front matter (`title:`, `keywords:` with English search terms). Merge duplicates, drop what is clearly stale, never copy secret values. Commit each source with `MT commit -k migrate -t <topic> -m "<summary>" -b "<where it came from>"`. Once the user confirms the import, offer to delete the old files.
5. **Pins.** If the user has memories they want pinned (always loaded, changed only on their explicit request), write each to `pinned/<slug>.md` and commit it with `-k pin`.
6. **Codex only:** tell the user to open `/hooks` in Codex and trust the memorytree hooks. Codex runs no plugin hook until they are trusted.
6b. **Claude Code: read-only access.** Offer to add these allow rules to `~/.claude/settings.json` (merge, keep everything else), so the agent can answer from memory without asking every time: `Read(~/.memorytree/**)`, `Bash(git -C ~/.memorytree log:*)`, `Bash(git -C ~/.memorytree show:*)`, plus the same two with the absolute home path. All of them only read. Don't add a rule for `memorytree search`: its path changes with every version, and a wildcard there would also approve other commands.
7. **Cost and models.** Tell the user that each turn runs one call to a cheap model in the background (Haiku on Claude Code, gpt-6-luna on Codex), billed to the open account. Models and limits live in `~/.memorytree/config`.
8. **Restart.** Hooks load at session start: the user must open a new session for memorytree to take effect.
9. **Check.** `MT search <a term from a migrated memory>` finds it. In a new session, the injected context starts with "memorytree is active".
