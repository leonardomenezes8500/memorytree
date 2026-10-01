# memorytree: design

Status: draft for discussion. There is no code yet.

## 1. Problem

LLM coding agents (Claude Code, Codex, and others) each keep their own memory, and that memory lives on one machine under one account. Someone who works across several machines, accounts and agents has to explain the same context again in every session. Sessions also end early to save tokens, so anything that wasn't saved explicitly is lost.

Recalling anything costs tokens: an agent only knows what is in its context window. The goal is not free memory. It is to spend only the tokens the user would have spent explaining things by hand, and to stop spending them more than once.

## 2. Idea

memorytree is **git for AI memory**. `~/.memorytree/` is a git repository, and each git concept maps to one memory concept:

- a **blob** is the content of one memory;
- a **tree** is how memories are organized;
- a **commit** is one memory event, and **its message is the index**;
- the **history** is how ideas evolved;
- **refs** (branches, tags, notes) give the same memories other views.

### The path is memory

Going from idea A to idea D is information in itself. The current state says *what* is true now. The history says *how* we got there and *why* the other ideas were dropped. That path keeps agents from re-proposing a discarded idea, and it reveals patterns in how the user works. memorytree never forgets an idea. It moves it out of the current state and keeps the path in history.

### A 4D graph

The memories form a graph with three dimensions of space and one of time:

| Dimension | Edges come from |
|---|---|
| Space 1: hierarchy | the tree, meaning folders and paths |
| Space 2: references | explicit links between memories (`[[path]]`) and `Supersedes:` / `Relates:` trailers |
| Space 3: co-change | memories changed in the same commit are related, even with no explicit link |
| Time | the commit history, with tags as named moments |

Every edge is derived from plain git data. No separate graph database exists, and the graph can always be rebuilt from the repository. A future visualization (section 13) draws exactly this graph.

## 3. Principles

1. **Git is the engine.** memorytree adds memory semantics on top of git and never reimplements what git already does: storage, hashing, history, search, sync, merge, config, hooks.
2. **Minimal dependencies.** Git is required. Python 3 (standard library only) runs the hooks and the search index (Q1).
3. **No escape.** While memorytree is active, an agent cannot skip reading it or save memory anywhere else (section 9).
4. **Memory is for models, docs are for people.** Whatever loads into an agent's context on its own (memories, pinned rules, the commandments, CLAUDE.md, AGENTS.md) is compiled for tokens: inject the relevant slice, never the whole store, as dense facts. `core.mode = economy` (the default) loads each pinned memory as its one-line `rule:`; `full` trades tokens for prose. A PreToolUse hook (Claude Code; Codex has none) refuses an edit that grows a CLAUDE.md or AGENTS.md past `core.maxInstructionChars`. Project docs (README, DESIGN, ROADMAP) are read on demand by people and agents alike, so they are written for humans: descriptive, the why in full, never compressed to save tokens. The instruction file links to them instead of repeating them.
5. **English, always.** Code, docs, memories, keywords and commit messages are in English. The only exception is text that must be kept verbatim in its original language (a quote, a hardcoded UI string); it is stored as-is and marked as verbatim.
6. **The user owns the data.** The vault is a private repository the user controls. memorytree ships no server and no telemetry.

## 4. Repository layout

```
~/.memorytree/                 a git repository (the vault)
  .git/
  config                       memorytree settings, git-config format (section 11)
  COMMANDMENTS.md              the rules every agent follows (section 8)
  user/
    profile.md                 who the user is and how agents should behave (always loaded)
  pinned/<slug>.md             memories the user explicitly endorsed (always loaded, protected)
  projects/<name>/
    overview.md                purpose, status, where it lives
    decisions.md               current decisions (the history holds the path)
  env/
    machines.md, accounts.md, storage.md
  topics/<name>.md             knowledge that isn't tied to one project
```

The layout is a convention enforced by the pre-commit hook (section 9). It is not hardcoded in the tools, and folders can be added later.

## 5. Memory file format

```markdown
---
title: Short title
keywords: english search terms
links: projects/foo/overview, env/storage
---

The fact, why it matters, how to apply it.
```

A memory is the current truth about one subject. To change it, edit the file and commit; never append a dated log. The log is git's job.

## 6. Commit messages are the index

Each commit records one memory event. A full memory commit looks like this:

```
decision(project-x): drop custom search, use git grep

Keyword search inside git covers the current corpus with no extra
dependency. Ruled out: a local vector search tool (2 GB of models per
machine, seconds of latency per prompt).

Kind: decision
Topic: project-x, search
Supersedes: 3f9a2c1
Agent: claude-code
Machine: work-pc-1
Session: 8a50c254
```

- **Subject:** `kind(topic): summary`. It reads well in `git log --oneline` and `git log --grep` can find it.
- **Body:** why the change happened and what was ruled out. This is where the path from A to D lives.
- **Trailers:** structured fields that `git log --format='%(trailers:key=Kind)'` and `git interpret-trailers` can read without parsing prose.

| Trailer | Values | Purpose |
|---|---|---|
| `Kind` | memory: `fact`, `decision`, `preference`, `correction`, `idea`, `abandon`, `migrate`, `pin`, `unpin`; tracking: `issue`, `progress`, `close`, `milestone`, `sprint`, `release` | the type of event; filter history by it |
| `Issue` | `<project>/<slug>` | tracking edge: the roadmap issue this event relates to (section 14) |
| `Topic` | comma-separated | cross-cutting index, independent of folders |
| `Supersedes` | commit hash | explicit time edge: this replaces that |
| `Relates` | path or hash | explicit space edge |
| `Agent`, `Machine`, `Session` | free text | provenance (who learned this, where, when) |

## 7. Git features, used to the full

| Git feature | memorytree use |
|---|---|
| blob | memory content, deduplicated by hash |
| tree | layout and hierarchy (space 1) |
| commit + message + trailers | memory events and the index (section 6) |
| `git log`, `--follow` | the path of one memory or topic over time |
| `git log --grep`, `-S`, `-G` | search history: "when and why did we change X?" |
| `git grep` | search the current state |
| `git blame` | provenance of each line |
| `main` | current truth: what agents load |
| branches `explore/<idea>` | an idea under exploration, kept apart from `main` until accepted |
| tags `archived/<idea>` | an abandoned idea frozen in place: searchable, never auto-loaded |
| tags `moment/<name>` | named points in time ("before the rewrite") |
| `git notes` (`refs/notes/hindsight`) | later judgments attached to an old commit without rewriting it, e.g. "this decision turned out wrong because…" |
| pre-commit / commit-msg hooks | enforce format and commandments on the data (section 9) |
| `git config -f config` | settings in git's own format |
| remotes, push/pull | sync across machines |
| merge | two machines saved at once; conflicts on one memory are resolved by an agent |

## 7a. Depth levels

Branches and tags are different things: a **branch** is a pointer that moves (a line of thought that is still growing), and a **tag** is a pointer that never moves (a frozen moment). memorytree uses each for a different concept and arranges every ref into levels. Each level is harder to reach and holds more abstract memory than the one before it. Agents start at level 0 and go deeper only when they need to.

| Level | Git object | Holds | Abstraction | Loaded |
|---|---|---|---|---|
| 0 | `main:user/profile.md`, `main:pinned/` | who the user is, how agents behave, what the user explicitly endorsed | identity | every session |
| 1 | files on `main` | current truth: facts, decisions, preferences | concrete | injected per prompt when relevant |
| 2 | history of `main` (messages, trailers, diffs) | how and why things changed: the path from A to D | causal | on search |
| 3 | branches `explore/<idea>` | live alternatives still being developed, not accepted yet | hypothetical | on search, only when the idea comes up |
| 4 | tags `archived/<idea>`, `moment/<name>` | abandoned ideas and named points in time, frozen | historical | on explicit search |
| 5 | notes `refs/notes/hindsight` | judgments made later about old commits, and patterns across ideas ("this user tends to start big and simplify") | reflective | on explicit search; patterns that prove stable get promoted to level 0 |

Lifecycle of an idea: it starts on `explore/<idea>`. If accepted, it is merged into `main` and the branch is deleted (history keeps it). If abandoned, it is tagged `archived/<idea>` with an `abandon` commit explaining why, and the branch is deleted. Hindsight about either outcome goes to level 5.

## 7b. Pinned memories

Most memories are inferred: the capture model decides what was worth keeping. A **pinned** memory is different, because the user endorsed it explicitly ("I want this as a standard", "pin this"). It is the strongest signal there is.

- Lives in `pinned/<slug>.md` and is loaded in every session (level 0). There are few of them and they are short. Each pinned memory carries a one-line `rule:` in its front matter: that line travels inside the commandments block in each agent's global instructions (subagents read those files but never see hook injections), while the full text stays in the vault for search. Everything loaded every session is kept to a few hundred tokens.
- Protected: the capture model may never edit or delete one. Only an explicit user request changes it, through a `pin` or `unpin` commit. The pre-commit hook rejects any other commit that touches `pinned/`.
- When the user praises something without asking to pin it, the capture model records it as a `preference` and suggests pinning it. It never pins on its own.
- `git log --grep "Kind: pin"` is the history of everything the user has endorsed.

## 8. Commandments

`COMMANDMENTS.md` is versioned in the vault, and setup points each agent's global instructions at it (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`). It's kept short because it loads in every session. Draft:

1. memorytree is your only memory. Never use a built-in memory feature, and never write memory anywhere else.
2. Before you ask the user or explore the filesystem about a name, project, decision or preference, search memorytree (`memorytree search <english terms>`). The user may write in any language; you always search in English.
3. Search by depth (section 7a): injected memories → current state → history → explorations → archive → hindsight. Go one level deeper only when the level above doesn't answer.
4. The current state tells you *what*; history tells you *why*. Before proposing something, check whether it was already tried and abandoned.
5. Capture happens automatically. If the user corrects you or decides something, make sure it reaches memorytree in the commit format.
6. One memory per subject. Edit it; don't duplicate it. Never store secret values, only where they live.

## 9. Enforcement: no escape

Instructions are requests, and a model can ignore them. memorytree therefore enforces at three layers:

| Layer | Mechanism | Guarantees |
|---|---|---|
| Instructions | commandments in each agent's global instructions | the model knows the rules and the search order |
| Agent hooks (Claude Code and Codex plugins) | `SessionStart`: load profile + commandments, pull. `UserPromptSubmit`: search and inject relevant memories. `Stop`: capture the turn in the background and commit. `PreToolUse`: deny writes to native memory locations and direct edits under `~/.memorytree` that bypass the tool | recall and capture happen whether or not the model "decides" to |
| Git hooks in the vault | `pre-commit`: layout, front matter, secret scan. `commit-msg`: subject format and required trailers | nothing malformed enters the store, whichever agent or human commits |

**Activation gate:** if an agent's native memory is on, memorytree refuses to run, says why, and offers to turn it off (Claude Code: `autoMemoryEnabled: false`; Codex: `[features] memories = false`).

## 10. Lifecycle

1. **Session start:** pull with rebase, then inject the user profile and a pointer to the commandments.
2. **Every prompt:** search the current state with the prompt's terms, then inject the top N memories, at most once per session each.
3. **Every turn end:** a detached process gives the exchange plus related memories to a cheap model (Haiku on Claude Code, the cheapest model on Codex). The model returns file edits plus a commit message in the section 6 format. memorytree validates them, commits and pushes. The process survives the session ending.
4. **Conflicts:** pull with rebase. A conflict on a memory file is handed to the cheap model with both versions and resolved as a `correction` commit.

## 11. Setup and config

`memorytree init` (or the plugin's setup skill):

1. Detect the installed agents.
2. Gate: native memory must be off; offer to turn it off.
3. Clone the user's existing vault or create one (private remote).
4. **Generate `~/.memorytree/config` with every setting at its default** (below), unless the cloned vault already has one.
5. Install the commandments pointer in each agent's global instructions.
6. Offer to migrate existing native memories into the layout, one `migrate` commit per source.
7. Install the vault's git hooks.

Every tunable lives in the config file, including which model each agent uses for each job. Nothing is hardcoded and no environment variables are needed. A key missing from the file falls back to the same default that `init` writes.

```ini
[core]
    version = 1
    mode = economy           # economy | full: how compact memories, pinned rules and commandments are kept
    maxInstructionChars = 4000  # a CLAUDE.md/AGENTS.md edit may not grow it past this
[recall]
    maxMemories = 3          # memories injected per prompt
    maxChars = 1500          # characters per injected memory
    minScore = 2.0           # BM25 cutoff, applied once the vault has 30+ memories
    prefetch = true          # meaning-based recall through the capture call (Q1b)
    blockingExpand = false   # also expand each prompt synchronously (~4 s per prompt)
[capture]
    enabled = true
    maxPromptChars = 6000
    maxAnswerChars = 12000
[sync]
    pull = session-start     # session-start | never
    push = after-capture     # after-capture | manual
[agent "claude-code"]
    captureModel = haiku
    expandModel = haiku
[agent "codex"]
    captureModel = gpt-6-luna
    expandModel = gpt-6-luna
    reasoningEffort = low
```

The file is read with `git config -f ~/.memorytree/config <key>`. It is versioned, so every machine shares the same settings. Per-machine overrides go in the vault's `.git/config`, with the same keys under a `memorytree.` prefix. The remote URL is git's own business (`git remote`) and is not duplicated here.

## 12. Text only

memorytree stores text. Images, videos and other binaries stay where they are; a memory may describe one and point to its path or URL, nothing more.

## 13. Visualization (future)

Render the 4D graph: memories are nodes; edges come from hierarchy, links and trailers, and co-change; a time slider moves through commits; tags mark moments; archived ideas appear as faded branches. Everything is derived from the repository, so no extra data has to be stored now beyond what sections 5 and 6 already require.

## 14. Project tracking: break the stone

Every project is broken down **inside its own repository**, in a `ROADMAP.md` at the root. Milestones are outcomes, sprints are batches of work, and issues are the pieces, each with a "done when". This is a development standard for every project, and it replaces any hosted issue tracker. This repository's [ROADMAP.md](ROADMAP.md) is the reference.

```markdown
## Sprint 1

### M1 Core vault: `memorytree init` creates a working vault

1. [x] `cli-skeleton`: … Done when `memorytree --help` lists the commands.
2. [ ] `config`: … Done when a missing key returns its default.
```

- **The plan lives with the code.** The roadmap is versioned with the work it describes, the README links it, and anyone opening the repo sees the plan without any extra tool.
- **Commits close issues.** The commit that finishes an issue checks its box in `ROADMAP.md` and carries `Issue: <project>/<slug>`, so `git log --grep "Issue: <project>/<slug>"` is the issue's timeline.
- **Milestones and sprints are tags in the project repo:** `milestone/<name>` and `sprint/<n>`, placed on the commit that finished them. A sprint closes with a short retrospective in its tag message; lessons that apply beyond the project go to the vault at level 5.
- **Dropping is not deleting.** A dropped issue is struck through with the reason, and the path stays visible.
- **IDs are slugs.** Numbers only give order within the file.

memorytree's role:

- The commandments tell agents to read the project's plan before working in it: `ROADMAP.md` for projects that follow this standard, otherwise whatever the project uses (an issue tracker named in its instructions, its README); with no plan at all, the project's recent `git log` plus its vault memories. Never the whole codebase. memorytree works the same for users who don't follow this standard.
- The capture call records progress in the vault (`progress` and `close` events with `Issue:` trailers) along with the context and decisions behind the work, which the roadmap file does not hold.
- `memorytree status [project]` reads `ROADMAP.md` across the user's known projects and shows milestone progress and the current sprint.
- The vault keeps the memory *about* a project (`projects/<name>/`: overview, decisions, where it lives). The repo keeps its *plan*. Neither duplicates the other.

## 15. Decisions

- **Q1 Search engine: SQLite FTS5 (BM25) through Python's standard library.** The index is derived from git and covers both the files on `main` and every commit message, so history is searchable the same way the current state is. It updates incrementally: `git diff --name-only <indexed>..HEAD` plus `git log <indexed>..HEAD`. It lives in a cache dir and can be deleted and rebuilt at any time. Measured latency is about 50 ms per prompt, it costs zero tokens and it downloads nothing.
  - Ruled out for now: plain `git grep` has no ranking, so it would inject noise; local semantic search needs a ~0.3 to 2 GB model on every machine and adds seconds per prompt unless a daemon keeps the model loaded.
  - Revisit if real misses show up. Semantic search could then be added over the same files.
- **Q2 Language: English everywhere** (principle 5). The automatic recall matches language-neutral terms such as names, paths and project names. For concepts, the agent searches in English itself (commandment 2), which costs a few tokens and only happens when it's needed.
- **Q3 Branches vs tags:** separate concepts, arranged as depth levels (section 7a).

- **Q1b Meaning-based recall through the cheap model.** Measured on 2026-09-30: one Haiku or gpt-6-luna call takes about 4 s, which is too slow to block every prompt. Instead, the capture call that already runs after every turn (lifecycle step 3) also returns `next_terms`: English keywords describing what the conversation is about. memorytree searches with them in the background and stores the hits as *prefetched* for the session. The next prompt injects prefetched memories together with the FTS hits for its own words. Meaning-based recall therefore adds zero latency and zero extra model calls. It only misses on a session's first prompt, which is covered by the FTS hits and commandment 2. The setting `recall.blockingExpand = true` opts into the 4 s synchronous expansion for users who prefer it.
- **Q4 Media:** out of scope. memorytree stores text only (section 12).
- **Q5 Capture:** runs after every turn, in the background, with no latency for the user.
- **Q6 Agents:** Claude Code and Codex first. Other major agents (Cursor, Gemini CLI, …) are a roadmap issue.
- **Q7 Tracking:** each project's plan lives in its own repository's `ROADMAP.md` (section 14). No hosted issue tracker is used, including for memorytree itself.

## 16. First memories

The first memories the user wants pinned once memorytree runs:

1. **Simple first, depth on demand** (2026-09-30). Any doc, README or answer opens with the shortest form that says what it is and why, in a few direct lines, and links to the deeper material (e.g. `DESIGN.md`) instead of inlining it. The reference example is this repository's README.

2. **Break the stone** (2026-10-01). A development standard for every project: break it down inside its own repository, in a `ROADMAP.md` with milestones (outcomes) → sprints (batches) → issues (pieces), each with a "done when", worked in order. The commit that finishes an issue checks it off. There is no hosted tracker.
3. **Design, then README, then roadmap** (2026-10-01). Every project starts in this order: `DESIGN.md` (how it works, decided together until no open questions remain) → `README.md` (what it is and why, in a few lines, linking the design) → `ROADMAP.md` (the stone broken into pieces). Code comes after.
