"""Run: python3 test_memorytree.py"""
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
TMP = Path(tempfile.mkdtemp())
ENV = {**os.environ, "MEMORYTREE_DIR": str(TMP / "vault"),
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def mt(*args, ok=True):
    r = subprocess.run(["python3", str(ROOT / "bin" / "memorytree"), *args], env=ENV, capture_output=True, text=True)
    assert (r.returncode == 0) == ok, f"memorytree {args}: {r.returncode}\n{r.stdout}{r.stderr}"
    return r.stdout.strip()


# cli-skeleton
assert "config" in mt("--help")
assert mt("--version").startswith("memorytree ")

# config: defaults with no vault, canonical keys, subsections keep their case
assert mt("config", "recall.maxMemories") == "3"
assert mt("config", "agent.claude-code.captureModel") == "haiku"
assert "recall.maxmemories=3" in mt("config")
mt("config", "nope.key", ok=False)

print("ok")
