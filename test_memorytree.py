"""Run: python3 test_memorytree.py"""
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
TMP = Path(tempfile.mkdtemp())
VAULT = TMP / "vault"
os.environ.update(MEMORYTREE_DIR=str(VAULT), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                  GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

loader = importlib.machinery.SourceFileLoader("memorytree", str(ROOT / "bin" / "memorytree"))
m = importlib.util.module_from_spec(importlib.util.spec_from_loader("memorytree", loader))
loader.exec_module(m)


def mt(*args, ok=True):
    r = subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), *args], capture_output=True, text=True)
    assert (r.returncode == 0) == ok, f"memorytree {args}: {r.returncode}\n{r.stdout}{r.stderr}"
    return r.stdout.strip()


def git_log():
    return subprocess.run(["git", "-C", str(VAULT), "log", "--format=%B"], capture_output=True, text=True).stdout


# cli-skeleton
assert "config" in mt("--help")
assert mt("--version").startswith("memorytree ")

# config: defaults with no vault, canonical keys, subsections keep their case
assert mt("config", "recall.maxMemories") == "3"
assert mt("config", "agent.claude-code.captureModel") == "haiku"
assert "recall.maxmemories=3" in mt("config")
mt("config", "nope.key", ok=False)

# init-vault: an empty home gives a committed vault; running it again changes nothing
assert "created config, COMMANDMENTS.md" in mt("init")
assert "init(memorytree): create vault" in git_log() and "Kind: init" in git_log()
assert "(created" not in mt("init")

# config: per-machine overrides win over the vault file and the defaults
subprocess.run(["git", "-C", str(VAULT), "config", "memorytree.recall.maxMemories", "5"], check=True)
assert mt("config", "recall.maxMemories") == "5"

# commit-format: a good message commits with subject, body and trailers
(VAULT / "topics").mkdir()
(VAULT / "topics" / "search.md").write_text("---\ntitle: Search\nkeywords: search\n---\n\nUse FTS5.\n")
mt("commit", "-k", "decision", "-t", "search", "-t", "memorytree", "-m", "use FTS5",
   "-b", "Ruled out: git grep, no ranking.", "--issue", "memorytree/index-files")
for line in ("decision(search): use FTS5", "Ruled out: git grep", "Kind: decision",
             "Topic: search, memorytree", "Issue: memorytree/index-files"):
    assert line in git_log(), line
mt("commit", "-k", "decision", "-t", "search", "-m", "again", ok=False)  # nothing to commit

# commit-format: malformed messages are refused
assert m.validate_message("fact(env): NAS paths\n\nBody.\n\nKind: fact\nTopic: env, storage\n") == []
assert m.validate_message("Merge branch 'x'") == []
assert m.validate_message("updated stuff")
assert m.validate_message("fact(env): x\n\nKind: decision\nTopic: env\n")  # kind doesn't match
assert m.validate_message("fact(env): x\n\nKind: fact\nTopic: other\n")  # subject topic missing
assert m.validate_message("blah(env): x\n\nKind: blah\nTopic: env\n")  # unknown kind
assert m.validate_message("fact(env): x\nno blank line\n\nKind: fact\nTopic: env\n")

# vault-git-hooks: bad commits are refused even from plain git commit
def plain_commit(path, text, message):
    target = VAULT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    subprocess.run(["git", "-C", str(VAULT), "add", "-A"], check=True)
    r = subprocess.run(["git", "-C", str(VAULT), "commit", "-q", "-m", message], capture_output=True, text=True)
    if r.returncode:
        subprocess.run(["git", "-C", str(VAULT), "reset", "-q", "--hard"], check=True)
        subprocess.run(["git", "-C", str(VAULT), "clean", "-qfd"], check=True)
    return r.returncode == 0


NOTE = "---\ntitle: T\n---\n\nBody.\n"
FACT = "fact(env): x\n\nKind: fact\nTopic: env\n"
assert plain_commit("env/a.md", NOTE, FACT)
assert not plain_commit("env/b.md", NOTE, "updated stuff")  # message format
assert not plain_commit("misc/c.md", NOTE, FACT)  # outside the layout
assert not plain_commit("env/d.md", "no front matter\n", FACT)
assert not plain_commit("env/e.txt", "text\n", FACT)  # not markdown
assert not plain_commit("env/f.md", NOTE + "token ghp_" + "a" * 36 + "\n", FACT)  # secret
assert not plain_commit("pinned/style.md", NOTE, "fact(style): x\n\nKind: fact\nTopic: style\n")
assert plain_commit("pinned/style.md", NOTE, "pin(style): simple first\n\nKind: pin\nTopic: style\n")
assert not plain_commit("pinned/style.md", NOTE + "edited\n", "fact(style): x\n\nKind: fact\nTopic: style\n")


# search: index files and history on main, walk the depth levels in order
def vault_git(*args):
    return subprocess.run(["git", "-C", str(VAULT), *args], check=True, capture_output=True, text=True).stdout


(VAULT / "projects" / "radar").mkdir(parents=True)
(VAULT / "projects" / "radar" / "overview.md").write_text(
    "---\ntitle: Radar overview\nkeywords: radar, weather, previsão\n---\n\nA weather forecast tool.\n")
mt("commit", "-k", "fact", "-t", "radar", "-m", "radar forecasts weather")
out = mt("search", "radar")
assert out.index("== level 1") < out.index("projects/radar/overview.md") < out.index("== level 2")
assert "fact(radar): radar forecasts weather" in out
assert "projects/radar/overview.md" in mt("search", "previsao")  # accents ignored
assert "decision(search): use FTS5" in mt("search", "grep")  # found through the commit body (why)

# incremental: an edit shows up, a deleted memory disappears
(VAULT / "projects" / "radar" / "overview.md").write_text(
    "---\ntitle: Radar overview\nkeywords: radar\n---\n\nNow also tracks volunteers.\n")
mt("commit", "-k", "fact", "-t", "radar", "-m", "radar tracks volunteers")
assert "projects/radar/overview.md" in mt("search", "volunteers", "-d", "1")
(VAULT / "projects" / "radar" / "overview.md").unlink()
mt("commit", "-k", "abandon", "-t", "radar", "-m", "radar dropped", "-b", "Replaced by a multi-client tool.")
assert "projects/radar" not in mt("search", "volunteers", "-d", "1", ok=False)
assert "abandon(radar): radar dropped" in mt("search", "multi", "client")

# rewritten history rebuilds the index instead of drifting
vault_git("reset", "-q", "--hard", "HEAD~1")
assert "projects/radar/overview.md" in mt("search", "volunteers", "-d", "1")

# levels 3-5 come only with --depth, and in order
vault_git("checkout", "-q", "-b", "explore/vector-search")
(VAULT / "topics" / "vectors.md").write_text("---\ntitle: Vectors\n---\n\nTry embeddings for recall.\n")
mt("commit", "-k", "idea", "-t", "search", "-m", "try embeddings")
vault_git("checkout", "-q", "main")
vault_git("tag", "-a", "archived/graph-db", "-m", "abandon: graph database needs a server", "HEAD")
vault_git("notes", "--ref=hindsight", "add", "-m", "embeddings looked promising but cost too much", "HEAD")
assert "level 3" not in mt("search", "embeddings", ok=False)
deep = mt("search", "embeddings", "graph", "server", "-d", "5")
assert deep.index("== level 3") < deep.index("topics/vectors.md") < deep.index("== level 4") \
    < deep.index("archived/graph-db") < deep.index("== level 5")


# agents: hooks run with JSON on stdin, against a fake Claude/Codex home
HOMES = TMP / "homes"
os.environ.update(CLAUDE_CONFIG_DIR=str(HOMES / "claude"), CODEX_HOME=str(HOMES / "codex"))
os.environ.pop("CLAUDE_CODE_DISABLE_AUTO_MEMORY", None)


def hook(event, agent, payload):
    r = subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), "agent-hook", event, agent],
                       input=json.dumps(payload), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None


# a brand-new vault: the first session start works before anything was indexed
fresh = TMP / "fresh"
subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), "init"], env={**os.environ, "MEMORYTREE_DIR": str(fresh)},
               check=True, capture_output=True)
subprocess.run(["git", "init", "-q", "--bare", str(TMP / "fresh-remote.git")], check=True)
subprocess.run(["git", "-C", str(fresh), "remote", "add", "origin", str(TMP / "fresh-remote.git")], check=True)
(HOMES / "claude").mkdir(parents=True)
(HOMES / "claude" / "settings.json").write_text('{"autoMemoryEnabled": false}')
r = subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), "agent-hook", "session-start", "claude-code"],
                   input='{"session_id": "f1", "source": "startup"}', capture_output=True, text=True,
                   env={**os.environ, "MEMORYTREE_DIR": str(fresh)})
assert "memorytree is active" in r.stdout, r.stderr
(HOMES / "claude" / "settings.json").unlink()

# native-memory-gate: Claude's auto memory is on by default, so memorytree refuses to run
out = hook("session-start", "claude-code", {"session_id": "s1", "source": "startup"})
assert "NOT active" in out["additionalContext"] and "autoMemoryEnabled" in out["additionalContext"]
assert hook("prompt", "claude-code", {"session_id": "s1", "prompt": "radar"}) is None
(HOMES / "claude" / "settings.json").write_text('{"autoMemoryEnabled": false}')
(HOMES / "codex").mkdir(parents=True)
(HOMES / "codex" / "config.toml").write_text("[features]\nmemories = true\n")
assert "NOT active" in hook("session-start", "codex", {"session_id": "c1"})["additionalContext"]
(HOMES / "codex" / "config.toml").write_text("[features]\nmemories = false\n")
denied = hook("tool", "claude-code", {"tool_input": {"file_path": str(HOMES / "claude/projects/x/memory/a.md")}})
assert denied["permissionDecision"] == "deny"
assert hook("tool", "claude-code", {"tool_input": {"file_path": str(VAULT / "topics/a.md")}}) is None

# hook-session-start: profile and pinned memories are loaded
(VAULT / "user").mkdir(exist_ok=True)
(VAULT / "user" / "profile.md").write_text("---\ntitle: Profile\n---\n\nCalls the assistant Dante.\n")
mt("commit", "-k", "preference", "-t", "user", "-m", "assistant name")
start = hook("session-start", "codex", {"session_id": "c1", "source": "startup"})["additionalContext"]
assert "memorytree is active" in start and "Dante" in start
assert "## T (pinned/style.md)" in start

# hook-recall: naming a project recalls it, once per session
first = hook("prompt", "claude-code", {"session_id": "s2", "prompt": "como está o radar?"})
assert "projects/radar/overview.md" in first["additionalContext"]
assert hook("prompt", "claude-code", {"session_id": "s2", "prompt": "e o radar?"}) is None
assert hook("prompt", "claude-code", {"session_id": "s3", "prompt": "ok"}) is None
hook("session-start", "claude-code", {"session_id": "s2", "source": "clear"})
assert hook("prompt", "claude-code", {"session_id": "s2", "prompt": "radar"}) is not None

# commandments-install: a marked block, refreshed in place, removable, other content kept
(HOMES / "claude" / "CLAUDE.md").write_text("# my rules\n\nBe brief.\n")
mt("install")
claude_md = (HOMES / "claude" / "CLAUDE.md").read_text()
assert claude_md.startswith("# my rules") and "<!-- memorytree -->" in claude_md and "search <english" in claude_md
assert len(claude_md) < 1600  # the block loads every session: keep it small
assert "Hook check" in claude_md and "/hooks" in claude_md  # tells the user when hooks are not running
assert "# Pinned rules\n- Body." in claude_md  # subagents read this file too; a pin without `rule` loads its body
start = hook("session-start", "claude-code", {"session_id": "s10", "source": "startup"})["additionalContext"]
assert "Dante" in start and "pinned/style.md" not in start  # not injected twice
assert "memory events" not in start  # history loads only on request
shown = subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), "agent-hook", "session-start", "codex"],
                       input='{"session_id": "s11"}', capture_output=True, text=True).stdout
assert re.search(r"memorytree active: \d+ memories, 1 pinned", json.loads(shown)["systemMessage"])  # seen by the user
assert (HOMES / "codex" / "AGENTS.md").read_text().count("<!-- memorytree -->") == 1
assert "unchanged" in mt("install", "codex")
mt("install", "--uninstall")
assert (HOMES / "claude" / "CLAUDE.md").read_text().strip() == "# my rules\n\nBe brief."

# capture: a fake cheap model, configured like any other agent command
import time

FAKE = TMP / "fake_model.py"
FAKE.write_text("""import json, sys
prompt = sys.stdin.read()
if "<version_a>" in prompt:
    print("---\\ntitle: Merged\\n---\\n\\nmerged A and B")
else:
    print(open(sys.argv[1]).read())
""")
CANNED = TMP / "canned.json"


def fake(output):
    CANNED.write_text(json.dumps(output))
    subprocess.run(["git", "-C", str(VAULT), "config", "memorytree.agent.claude-code.command",
                    f"python3 {FAKE} {CANNED}"], check=True)


def capture_turn(session, prompt, answer):
    hook("prompt", "claude-code", {"session_id": session, "prompt": prompt})
    r = subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), "agent-hook", "stop", "claude-code"],
                       input=json.dumps({"session_id": session, "last_assistant_message": answer}),
                       capture_output=True, text=True)
    assert r.stdout.strip() == "{}"  # Codex requires JSON from Stop hooks
    queue = Path(vault_git("rev-parse", "--absolute-git-dir").strip()) / "memorytree" / "queue"
    for _ in range(100):  # the capture runs detached
        if not any(queue.glob("*.json")):
            assert not any(queue.glob("*.failed")), (queue.parent / "capture.log").read_text()
            return
        time.sleep(0.1)
    raise AssertionError("capture did not finish")


fake({"memories": [{"path": "topics/storage.md", "title": "Storage", "keywords": "sqlite, storage",
                    "body": "Use SQLite. Key ghp_" + "b" * 36 + " lives in pass."}],
      "commit": {"kind": "decision", "topics": ["Storage Engine"], "summary": "use sqlite for storage" + " because" * 12,
                 "body": "Ruled out: a server database."},
      "next_terms": "radar weather forecast"})
capture_turn("s5", "decidimos usar sqlite?", "Yes, SQLite.")
log = git_log()
assert "decision(storage-engine): use sqlite for storage because" in log and max(map(len, log.splitlines())) <= 72 and "becaus\n" not in log and "Ruled out: a server database." in log
assert "Agent: claude-code" in log and "Session: s5" in log
stored = (VAULT / "topics" / "storage.md").read_text()
assert "Use SQLite." in stored and "ghp_" not in stored  # secret redacted, memory kept

# prefetch: the next prompt recalls what the conversation is about, even with no matching words
nxt = hook("prompt", "claude-code", {"session_id": "s5", "prompt": "ok, e agora?"})
assert "projects/radar/overview.md" in nxt["additionalContext"]

# capture-apply: paths outside the layout are dropped; nothing worth keeping commits nothing
head = vault_git("rev-parse", "HEAD")
fake({"memories": [{"path": "../escape.md", "body": "x"}, {"path": "misc/a.md", "body": "x"}],
      "commit": {"kind": "fact", "topics": ["x"], "summary": "x"}})
capture_turn("s6", "nada", "nada")
fake({"memories": [], "next_terms": "nothing"})
capture_turn("s6", "ok", "ok")
assert vault_git("rev-parse", "HEAD") == head and not (TMP / "escape.md").exists()

# a refused capture (pinned without an explicit pin) puts back exactly what it touched
pinned_before = (VAULT / "pinned" / "style.md").read_text()
fake({"memories": [{"path": "pinned/style.md", "title": "T", "body": "rewritten"}],
      "commit": {"kind": "preference", "topics": ["style"], "summary": "rewrite style"}})
capture_turn("s7", "gostei", "ok")
assert (VAULT / "pinned" / "style.md").read_text() == pinned_before
assert vault_git("rev-parse", "HEAD") == head and not vault_git("status", "--porcelain").strip()

# conflict-resolution: two machines change one memory; the model merges it and the push goes through
remote = TMP / "remote.git"
subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
vault_git("remote", "add", "origin", str(remote))
vault_git("push", "-q", "-u", "origin", "main")
other = TMP / "other"
subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), "init", "--clone", str(remote)],
               env={**os.environ, "MEMORYTREE_DIR": str(other)}, check=True, capture_output=True)
(other / "topics" / "storage.md").write_text("---\ntitle: Storage\n---\n\nB says Postgres later.\n")
subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), "commit", "-k", "fact", "-t", "storage", "-m", "b"],
               env={**os.environ, "MEMORYTREE_DIR": str(other)}, check=True, capture_output=True)
subprocess.run(["git", "-C", str(other), "push", "-q"], check=True)
fake({"memories": [{"path": "topics/storage.md", "title": "Storage", "body": "A says SQLite only."}],
      "commit": {"kind": "fact", "topics": ["storage"], "summary": "a"}})
capture_turn("s8", "sqlite", "sqlite")
assert "merged A and B" in (VAULT / "topics" / "storage.md").read_text()
assert vault_git("rev-parse", "HEAD") == vault_git("rev-parse", "origin/main")  # pushed
assert not vault_git("status", "--porcelain").strip()

# plugin updates delete the old script: the vault's git hooks fall back to the newest installed copy
hook_file = Path(vault_git("rev-parse", "--absolute-git-dir").strip()) / "hooks" / "pre-commit"
hook_file.write_text(hook_file.read_text().replace(str((ROOT / "bin" / "memorytree").resolve()), "/gone/memorytree"))
assert not plain_commit("env/g.md", NOTE, FACT)  # nothing installed: refused, never silently skipped
installed = HOMES / "claude" / "plugins" / "cache" / "memorytree" / "memorytree" / "9.9.9" / "bin"
installed.mkdir(parents=True)
(installed / "memorytree").write_text((ROOT / "bin" / "memorytree").read_text())
assert plain_commit("env/g.md", NOTE, FACT)
assert not plain_commit("env/h.md", "no front matter\n", FACT)  # and it still enforces

# recall skips only what session start already loaded (profile, pinned), not every user/ memory
(VAULT / "user" / "ui-checks.md").write_text("---\ntitle: UI checks\nkeywords: viewport, firefox\n---\n\nCheck 320 px.\n")
mt("commit", "-k", "preference", "-t", "user", "-m", "ui checks")
assert "user/ui-checks.md" in hook("prompt", "claude-code", {"session_id": "s9", "prompt": "viewport firefox"})["additionalContext"]

# sync: concurrent session starts and captures share one lock, so pulls never race on FETCH_HEAD
procs = [subprocess.Popen(["python3", str(ROOT / "bin" / "memorytree"), "sync"], stderr=subprocess.PIPE, text=True)
         for _ in range(4)]
assert all(p.wait() == 0 and "multiple branches" not in p.stderr.read() for p in procs)

print("ok")
