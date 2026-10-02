# Roadmap

The stone, broken into pieces. Milestones are outcomes, sprints are batches of work, and issues are the pieces. Do them in order; each issue is done when its "done when" holds. The commit that finishes an issue checks its box. See DESIGN.md §14.

## Sprint 1

### M1 Core vault: `memorytree init` creates a working vault

1. [x] `cli-skeleton`: a single-file Python CLI using only the standard library. Done when `memorytree --help` lists the commands.
2. [x] `config`: defaults, read through `git config -f`, with `.git/config` overrides. Done when a missing key returns its default.
3. [x] `init-vault`: create or clone the vault, create the layout, generate the config and `COMMANDMENTS.md`. Done when `init` on an empty home gives a committed vault.
4. [x] `commit-format`: `memorytree commit` writes the subject, body and trailers. Done when a malformed message is refused.
5. [x] `vault-git-hooks`: a pre-commit hook (layout, front matter, secret scan, pinned protection) and a commit-msg hook (format, trailers). Done when bad commits are refused even from plain `git commit`.

## Sprint 2

### M2 Search: find the right memory in ~50 ms

6. [x] `index-files`: an FTS5 index of the files on `main`, updated incrementally per commit. Done when an edit shows up in search.
7. [x] `index-history`: commit messages and trailers go into the index. Done when "why did we drop X" finds the `abandon` commit.
8. [x] `search-cmd`: `memorytree search` walks the depth levels (main → history → explore → archived → notes). Done when each level is reachable and ordered.

### M3 Agents: Claude Code and Codex read memorytree on their own

9. [x] `plugin-manifests`: Claude Code and Codex plugins from one repo, plus a marketplace. Done when both install from GitHub.
10. [x] `hook-session-start`: pull, then inject the profile, pinned memories and the commandments pointer. Done when a fresh session knows the user.
11. [x] `hook-recall`: inject relevant memories on each prompt, at most once per session. Done when naming a project recalls it.
12. [x] `native-memory-gate`: refuse to run while native memory is on, offer to turn it off, and block writes to native memory paths. Done on both agents.
13. [x] `commandments-install`: point `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` at the commandments. Done when both agents follow the search order.

## Sprint 3

### M4 Capture: every turn is remembered without asking

14. [x] `capture-hook`: a detached capture after each turn, using the cheap model from config. Done when closing the session right away still captures.
15. [x] `capture-apply`: validate the model output, write the files, commit and push. Done when bad output is rejected and good output is committed in the right format.
16. [x] `prefetch`: `next_terms` from the capture call feeds the next prompt's recall. Done when a Portuguese prompt recalls an English memory on the second turn.
17. [x] `conflict-resolution`: two machines capture at once, and the model resolves the conflict as a `correction`. Done when a forced conflict merges cleanly.

### M5 Go live: memorytree replaces native memory on every machine

18. [ ] `setup-skill`: the plugin's setup skill wraps `init`, the gate, migration and pins. Done when a new machine is fully set up from one command.
19. [x] `migrate-native`: import native Claude Code and Codex memories. Done when the old memories are found by search.
20. [x] `pin-first-memories`: pin the first memories from DESIGN.md §16. Done when a fresh session on any machine loads them.

## Sprint 4

### M6 Tracking: the vault is the project tracker

21. [ ] `issue-lifecycle`: agents take the next unchecked issue, check it off in the commit that finishes it, and capture records the progress in the vault. Done when finishing work closes its issue with no prompt from the user.
22. [ ] `status-cmd`: `memorytree status [project]` reads `ROADMAP.md` across known projects and shows milestone progress and the current sprint. Done when it matches the files.
23. [ ] `milestone-sprint-tags`: tag milestones and sprints in the project repo, and close a sprint with a retrospective. Done when `git tag` shows the timeline.

### M7 Depth: ideas have a lifecycle

24. [ ] `explore-archive`: `explore/<idea>` branches, plus promoting an idea to `main` or archiving it as `archived/<idea>`. Done when an abandoned idea is searchable but never auto-loaded.
25. [ ] `hindsight-notes`: later judgments recorded as git notes, with patterns that keep holding promoted to level 0. Done when a note shows up in level-5 search.
26. [x] `pin-levels`: a `level: 2` pin loads only `[keys] → path` and the agent reads the file when a task touches a key (DESIGN.md Q8). Done when a level-2 pin's rule is absent from CLAUDE.md, its keys and path are there, and a level-2 pin without keys is refused.

### M8 Trust: capture never loses a fact silently

27. [ ] `capture-no-silent-delete`: capture may delete or overwrite a memory only for a decision or correction the user stated, never for a proposal still under discussion (on 2026-10-01 a proposal was taken as a decision and memories were deleted). Done when a proposal turn leaves every existing memory intact and a stated decision still updates it.

## Sprint 5

### M9 Tree: pinned rules form a tree that the CLI walks and grows

28. [x] `make-install`: `make install` puts the CLI in `$(PREFIX)/bin` (`~/.local` by default), `make uninstall` removes it. Done when both work with a custom PREFIX.
29. [x] `show-cmd`: `memorytree show <node>` prints a pin's rule and its children's keys, so key lines need no path (`[shell|sh] → scripts/posix-shell`). Done when walking from a root key to a leaf needs only `show`.
30. [x] `pin-tree`: pins nest by generality (`pinned/scripts.md` parents `pinned/scripts/posix-shell.md`); only root pins load into CLAUDE.md/AGENTS.md, a more general rule said later becomes the parent. Done when the current pins live in a tree and a fresh session still follows a leaf rule.
31. [x] `add-cmd`: `memorytree add "<text>"` has the cheap model place a memory in the tree (creating a parent when it is more general) and commit it; for a pin it proposes the place and waits for the user's confirmation. Done when an added rule lands under the right parent with no expensive-model tokens spent.

## Later

- Other agents (Cursor, Gemini CLI, …).
- The 4D visualization.
- Semantic search, if keyword search plus prefetch misses in real use.
