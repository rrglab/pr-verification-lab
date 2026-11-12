"""Fail closed on obvious private or sensitive files in a public PR fixture."""
from pathlib import Path
import re
import subprocess
import sys

BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".sqlite", ".db"}
BLOCKED_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
BLOCKED_PARTS = {"private", "customer-data", "production-dumps", "node_modules", ".venv"}
PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
]
paths = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
violations = []
for name in filter(None, paths):
    path = Path(name)
    if path.name in BLOCKED_NAMES or path.suffix.lower() in BLOCKED_SUFFIXES or BLOCKED_PARTS.intersection(path.parts):
        violations.append(f"Blocked path: {name}")
        continue
    if path.is_file() and path.stat().st_size <= 1024 * 1024:
        data = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(data) for pattern in PATTERNS):
            violations.append(f"Potential secret: {name}")
if violations:
    print("\n".join(violations), file=sys.stderr)
    sys.exit(1)
print("Public-scope heuristic checks passed. Manual provenance review is still required.")
