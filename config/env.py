from __future__ import annotations

import os
from pathlib import Path


def load_env(path: Path | None = None) -> None:
    """Load simple KEY=VALUE pairs from a local .env file.

    Existing process environment variables win over values in .env. This keeps
    CI, shell configuration, and explicitly supplied secrets authoritative.
    The parser intentionally supports the common .env syntax JARVIS needs:
    blank lines, comments, optional ``export``, and single/double quotes.
    """
    env_path = path or Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)
