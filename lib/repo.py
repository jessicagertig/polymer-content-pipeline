"""Files a run changes in the repo: the <slug>-output/ directories and the calendar CSV.

A run on a laptop writes them into the checkout, to be committed by hand. A run on GitHub Actions
also commits and pushes each file to the run's own branch as it writes it (see the workflow). The Lambda's
package is read-only, so there they stay in memory and push() commits them to GitHub
as one commit (settings.github_repo, settings.github_token).
"""

import json
import os
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Optional

from config.settings import settings
from lib.logging import get


log = get(__name__)

ROOT = Path(__file__).parent.parent
_staged: dict[str, str] = {}   # repo-relative path → text this run changed
_git_lock = threading.Lock()   # check_post saves from several threads


def reset() -> None:
    _staged.clear()


def read(rel_path: str) -> str:
    """The text this run staged for the file, else the file in the checkout."""
    if rel_path in _staged:
        return _staged[rel_path]
    return (ROOT / rel_path).read_text(encoding="utf-8")


def stage(rel_path: str, text: str) -> None:
    """Records the file for push() and writes it into the checkout when that is writable."""
    _staged[rel_path] = text
    path = ROOT / rel_path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as e:
        log.info(f"Checkout is read-only ({e.strerror}); {rel_path} will be pushed")
        return
    if os.environ.get("GITHUB_ACTIONS") == "true":
        _commit(rel_path)


def _commit(rel_path: str) -> None:
    """Commits the file to the run's branch and pushes it, so a later failure cannot lose it. A failure
    is logged; the workflow's last step commits whatever is left."""
    with _git_lock:
        def git(*args) -> subprocess.CompletedProcess:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        git("add", rel_path)
        if git("diff", "--cached", "--quiet").returncode == 0:
            return
        for args in (("commit", "-q", "-m", f"Save {rel_path}"), ("push", "-q")):
            done = git(*args)
            if done.returncode:
                log.warning(f"git {args[0]} for {rel_path} failed: {done.stderr.strip()}")
                return


def push(message: str) -> None:
    """One commit on settings.github_branch with every staged file, through the GitHub
    git-data API. Only a Lambda run pushes; a laptop run leaves committing to the person."""
    if not _staged or not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return
    if not (settings.github_repo and settings.github_token):
        raise RuntimeError("GITHUB_REPO and GITHUB_TOKEN must be set for the Lambda to commit its output")
    branch = settings.github_branch
    head = _api(f"git/ref/heads/{branch}")["object"]["sha"]
    base_tree = _api(f"git/commits/{head}")["tree"]["sha"]
    tree = _api("git/trees", {
        "base_tree": base_tree,
        "tree": [{"path": p, "mode": "100644", "type": "blob", "content": t} for p, t in _staged.items()],
    })["sha"]
    commit = _api("git/commits", {"message": message, "tree": tree, "parents": [head]})["sha"]
    _api(f"git/refs/heads/{branch}", {"sha": commit}, method="PATCH")
    log.info(f"Pushed {len(_staged)} file(s) to {settings.github_repo}@{branch}: {commit[:7]}")
    _staged.clear()


def _api(path: str, body: Optional[dict] = None, method: Optional[str] = None) -> dict:
    url = f"https://api.github.com/repos/{settings.github_repo}/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Authorization", f"Bearer {settings.github_token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)
