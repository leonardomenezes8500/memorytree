"""Run: python3 test_memorytree.py"""
import importlib.machinery
import importlib.util
import os
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

print("ok")
