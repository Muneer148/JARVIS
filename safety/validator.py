from __future__ import annotations

from pathlib import Path


def safe_destination(source: Path, destination: Path) -> tuple[bool, str]:
    source = source.resolve()
    destination = destination.resolve()
    if destination == source:
        return False, "Source and destination are identical"
    if destination.exists():
        return False, f"Destination already exists: {destination.name}"
    return True, "ok"


def validate_plan(downloads: Path, plan: dict[str, list[str]], allowed_categories: set[str]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    actual = {p.name for p in downloads.iterdir() if p.is_file()}

    for category, names in plan.items():
        if category not in allowed_categories:
            errors.append(f"Unknown category: {category}")
        for name in names:
            if name in seen:
                errors.append(f"Duplicate file in plan: {name}")
            seen.add(name)
            source = downloads / name
            destination = downloads / category / name
            if not source.is_file():
                errors.append(f"Source does not exist: {name}")
            ok, reason = safe_destination(source, destination)
            if not ok and source.exists():
                errors.append(f"{name}: {reason}")

    missing = actual - seen
    extra = seen - actual
    errors.extend(f"File missing from plan: {name}" for name in sorted(missing))
    errors.extend(f"Unknown file in plan: {name}" for name in sorted(extra))
    return errors
