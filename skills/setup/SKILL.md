---
name: setup
description: Set up memorytree on this machine - vault, built-in memory off, commandments, migration of existing memories, pins. Use when the user asks to set up or install memorytree, when memorytree reports it has no vault or is not active, or on a new machine.
---

# memorytree setup

`MT` below means `python3 <this plugin's root>/bin/memorytree`. Run the steps in order. Show the user what you are about to change outside the vault and wait for a yes. Read [DESIGN.md](../../DESIGN.md) only if a step is unclear.

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
7. **Check.** `MT search <a term from a migrated memory>` finds it. In a new session, the injected context starts with "memorytree is active".
