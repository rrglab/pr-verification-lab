"""Run SHA-pinned private PR tests in a disposable local Git worktree.

Never publishes source or raw logs. The target repository must already be
available locally; network access and arbitrary test commands are not used.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOWED_TESTS = ("tests/test_inbound_frontdoor.py", "tests/test_address_protocol.py",
                 "tests/test_protocol_address_wire.py", "tests/test_protocol_boundary.py")
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=True, timeout=30).stdout.strip()


def verify(repo, expected_sha):
    if not SHA_RE.fullmatch(expected_sha):
        raise ValueError("invalid SHA")
    if not repo.is_dir() or not (repo / ".git").exists():
        raise ValueError("not a local git checkout")
    if git(repo, "status", "--porcelain"):
        raise ValueError("dirty source checkout")
    if git(repo, "cat-file", "-t", expected_sha) != "commit":
        raise ValueError("target commit unavailable")
    with tempfile.TemporaryDirectory(prefix="rrglab-verify-") as temporary:
        worktree = Path(temporary) / "source"
        git(repo, "worktree", "add", "--detach", str(worktree), expected_sha)
        try:
            if git(worktree, "rev-parse", "HEAD") != expected_sha:
                raise ValueError("target SHA mismatch")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *ALLOWED_TESTS],
                cwd=worktree, capture_output=True, text=True, timeout=120,
                check=False,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin",
                     "HOME": str(Path.home()), "PYTHONDONTWRITEBYTECODE": "1"},
            )
            # Never print captured stdout/stderr (may contain private code).
            status = "PASS" if result.returncode == 0 else "FAIL"
            code = result.returncode
        finally:
            git(repo, "worktree", "remove", "--force", str(worktree))
    return {"schema": "rrglab.local-pr-verification.v2",
            "target_sha": expected_sha, "test_profile": "justyou-inbound-v1",
            "result": status, "exit_code": code,
            "source_uploaded": False, "output_redacted": True,
            "temporary_worktree_removed": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    try:
        evidence = verify(args.repo.resolve(), args.sha)
    except (ValueError, subprocess.SubprocessError, OSError) as exc:
        evidence = {"schema": "rrglab.local-pr-verification.v2",
                    "target_sha": args.sha if SHA_RE.fullmatch(args.sha) else None,
                    "result": "BLOCKED", "reason": type(exc).__name__,
                    "source_uploaded": False, "output_redacted": True}
    print(json.dumps(evidence, sort_keys=True))
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
