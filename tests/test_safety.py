from pathlib import Path

from safety.validator import validate_plan


def test_duplicate_plan_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "a.txt"
    source.write_text("x")
    plan = {"Documents": ["a.txt"], "Other": ["a.txt"]}
    errors = validate_plan(tmp_path, plan, {"Documents", "Other"})
    assert any("Duplicate" in error for error in errors)


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    errors = validate_plan(tmp_path, {"Documents": ["missing.txt"]}, {"Documents"})
    assert any("does not exist" in error or "missing from plan" in error for error in errors)
