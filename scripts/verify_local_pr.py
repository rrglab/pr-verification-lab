"""Run an explicitly selected local private PR test without publishing source.

Public tool; requires a locally checked-out target and a pinned commit.
Only pre-approved pytest targets may be run. Output contains no source paths.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ALLOWED_TESTS = ("tests/test_inbound_frontdoor.py", "tests/test_address_protocol.py",
                 "tests/test_protocol_address_wire.py", "tests/test_protocol_boundary.py")


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            text=True, check=True, timeout=30)
    return result.stdout.strip()


def verify(repo, expected_sha):
    if not repo.is_dir() or not (repo / ".git").exists():
        raise ValueError("not a local git checkout")
    actual = git(repo, "rev-parse", "HEAD")
    if actual != expected_sha or len(expected_sha) != 40:
        raise ValueError("target SHA mismatch")
    if git(repo, "status", "--porcelain"):
        raise ValueError("dirty target checkout")
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", *ALLOWED_TESTS],
                            cwd=repo, capture_output=True, text=True, timeout=120, check=False)
    # Never publish raw output: it may include paths, private source or secrets.
    return {"schema": "rrglab.local-pr-verification.v1",
            "target_sha": actual, "test_profile": "justyou-inbound-v1",
            "result": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "test_count_expected": 17,
            "source_uploaded": False,
            "output_redacted": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    try:
        evidence = verify(args.repo.resolve(), args.sha)
    except (ValueError, subprocess.SubprocessError, OSError) as exc:
        evidence = {"schema": "rrglab.local-pr-verification.v1",
                    "target_sha": args.sha if len(args.sha) == 40 else None,
                    "result": "BLOCKED", "reason": type(exc).__name__,
                    "source_uploaded": False, "output_redacted": True}
    print(json.dumps(evidence, sort_keys=True))
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
