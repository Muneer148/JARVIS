from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from safety.validator import validate_plan

CATEGORY_EXTENSIONS: dict[str, set[str]] = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".ppt", ".pptx"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".flv"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Installers": {".exe", ".msi", ".msix", ".appx"},
    "Code": {".py", ".ipynb", ".java", ".c", ".cpp", ".h", ".hpp", ".js", ".ts", ".html", ".css", ".php", ".rb", ".go", ".rs"},
    "Data": {".csv", ".json", ".xml", ".sql", ".xlsx", ".xls"},
}

ALLOWED_CATEGORIES = set(CATEGORY_EXTENSIONS) | {"Other"}


def _category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "Other"


def build_plan(downloads: Path) -> dict[str, list[str]]:
    plan = {category: [] for category in ALLOWED_CATEGORIES}
    for path in sorted(downloads.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file():
            plan[_category_for(path)].append(path.name)
    return {category: names for category, names in sorted(plan.items()) if names}


def analyze_downloads(downloads: Path) -> dict[str, Any]:
    if not downloads.exists():
        return {"status": "error", "error": f"Downloads directory does not exist: {downloads}"}
    plan = build_plan(downloads)
    return {
        "status": "ok",
        "directory": str(downloads),
        "total_files": sum(len(v) for v in plan.values()),
        "categories": {k: len(v) for k, v in plan.items()},
        "plan": plan,
    }


def _format_plan(plan: dict[str, list[str]]) -> str:
    lines = ["Proposed organization:"]
    for category, names in plan.items():
        lines.append(f"  {category}: {len(names)} file(s)")
    lines.append(f"Total: {sum(len(v) for v in plan.values())} file(s)")
    return "\n".join(lines)


def execute_plan(downloads: Path, plan: dict[str, list[str]]) -> dict[str, Any]:
    errors = validate_plan(downloads, plan, ALLOWED_CATEGORIES)
    if errors:
        return {"status": "rejected", "errors": errors}

    moved: list[tuple[Path, Path]] = []
    try:
        for category, names in plan.items():
            destination_folder = downloads / category
            destination_folder.mkdir(exist_ok=True)
            for name in names:
                source = downloads / name
                destination = destination_folder / name
                shutil.move(str(source), str(destination))
                if source.exists() or not destination.exists():
                    raise RuntimeError(f"Verification failed after moving {name}")
                moved.append((source, destination))
        return {
            "status": "success",
            "planned_count": sum(len(v) for v in plan.values()),
            "moved_count": len(moved),
            "verified_count": len(moved),
        }
    except Exception as exc:
        rollback_errors: list[str] = []
        for source, destination in reversed(moved):
            try:
                if destination.exists() and not source.exists():
                    shutil.move(str(destination), str(source))
            except Exception as rollback_exc:
                rollback_errors.append(f"{source.name}: {rollback_exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "moved_before_failure": len(moved),
            "rollback_attempted": True,
            "rollback_errors": rollback_errors,
        }


def organize_downloads(downloads: Path) -> str:
    analysis = analyze_downloads(downloads)
    if analysis.get("status") != "ok":
        return str(analysis)
    plan = analysis["plan"]
    print("\n" + _format_plan(plan))
    answer = input("\nJARVIS wants permission to organize these files. Execute? (yes/no): ").strip().lower()
    if answer not in {"yes", "y"}:
        return "Organization cancelled. No files were moved."
    result = execute_plan(downloads, plan)
    return str(result)
