"""Tests for tools/filesystem.py and safety/validator.py"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from safety.validator import safe_destination, validate_plan
from tools.filesystem import (
    ALLOWED_CATEGORIES,
    CATEGORY_EXTENSIONS,
    _category_for,
    analyze_downloads,
    build_plan,
    execute_plan,
)


@pytest.fixture()
def downloads(tmp_path: Path) -> Path:
    d = tmp_path / "Downloads"
    d.mkdir()
    return d


def _touch(directory: Path, name: str) -> Path:
    path = directory / name
    path.write_text("", encoding="utf-8")
    return path


# ------------------------------------------------------------------
# Category detection
# ------------------------------------------------------------------


class TestCategoryFor:
    def test_pdf_is_document(self, tmp_path):
        assert _category_for(tmp_path / "report.pdf") == "Documents"

    def test_jpg_is_image(self, tmp_path):
        assert _category_for(tmp_path / "photo.jpg") == "Images"

    def test_mp4_is_video(self, tmp_path):
        assert _category_for(tmp_path / "clip.mp4") == "Videos"

    def test_mp3_is_audio(self, tmp_path):
        assert _category_for(tmp_path / "song.mp3") == "Audio"

    def test_zip_is_archive(self, tmp_path):
        assert _category_for(tmp_path / "backup.zip") == "Archives"

    def test_exe_is_installer(self, tmp_path):
        assert _category_for(tmp_path / "setup.exe") == "Installers"

    def test_py_is_code(self, tmp_path):
        assert _category_for(tmp_path / "script.py") == "Code"

    def test_csv_is_data(self, tmp_path):
        assert _category_for(tmp_path / "export.csv") == "Data"

    def test_unknown_extension_is_other(self, tmp_path):
        assert _category_for(tmp_path / "mystery.xyz") == "Other"

    def test_no_extension_is_other(self, tmp_path):
        assert _category_for(tmp_path / "README") == "Other"

    def test_uppercase_extension_matched(self, tmp_path):
        assert _category_for(tmp_path / "IMAGE.PNG") == "Images"


# ------------------------------------------------------------------
# build_plan
# ------------------------------------------------------------------


class TestBuildPlan:
    def test_empty_directory_returns_empty_plan(self, downloads):
        plan = build_plan(downloads)
        assert plan == {}

    def test_single_file_placed_correctly(self, downloads):
        _touch(downloads, "report.pdf")
        plan = build_plan(downloads)
        assert "Documents" in plan
        assert "report.pdf" in plan["Documents"]

    def test_directories_excluded_from_plan(self, downloads):
        (downloads / "subfolder").mkdir()
        plan = build_plan(downloads)
        assert plan == {}

    def test_multiple_categories(self, downloads):
        _touch(downloads, "photo.jpg")
        _touch(downloads, "song.mp3")
        _touch(downloads, "report.pdf")
        plan = build_plan(downloads)
        assert "Images" in plan
        assert "Audio" in plan
        assert "Documents" in plan

    def test_all_plan_categories_are_allowed(self, downloads):
        _touch(downloads, "unknown.xyz")
        plan = build_plan(downloads)
        for cat in plan:
            assert cat in ALLOWED_CATEGORIES


# ------------------------------------------------------------------
# analyze_downloads
# ------------------------------------------------------------------


class TestAnalyzeDownloads:
    def test_nonexistent_directory(self, tmp_path):
        result = analyze_downloads(tmp_path / "NoSuchFolder")
        assert result["status"] == "error"

    def test_valid_directory(self, downloads):
        _touch(downloads, "file.pdf")
        _touch(downloads, "image.png")
        result = analyze_downloads(downloads)
        assert result["status"] == "ok"
        assert result["total_files"] == 2
        assert "Documents" in result["categories"]
        assert "Images" in result["categories"]

    def test_empty_directory(self, downloads):
        result = analyze_downloads(downloads)
        assert result["status"] == "ok"
        assert result["total_files"] == 0


# ------------------------------------------------------------------
# execute_plan + rollback
# ------------------------------------------------------------------


class TestExecutePlan:
    def test_files_are_moved(self, downloads):
        _touch(downloads, "report.pdf")
        plan = {"Documents": ["report.pdf"]}
        result = execute_plan(downloads, plan)
        assert result["status"] == "success"
        assert (downloads / "Documents" / "report.pdf").exists()
        assert not (downloads / "report.pdf").exists()

    def test_empty_plan_succeeds(self, downloads):
        result = execute_plan(downloads, {})
        assert result["status"] == "success"
        assert result["moved_count"] == 0

    def test_missing_source_file_fails_validation(self, downloads):
        plan = {"Documents": ["ghost.pdf"]}
        result = execute_plan(downloads, plan)
        assert result["status"] == "rejected"

    def test_unknown_category_fails_validation(self, downloads):
        _touch(downloads, "file.pdf")
        plan = {"InvalidCategory": ["file.pdf"]}
        result = execute_plan(downloads, plan)
        assert result["status"] == "rejected"


# ------------------------------------------------------------------
# safe_destination
# ------------------------------------------------------------------


class TestSafeDestination:
    def test_same_source_and_destination_is_unsafe(self, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("")
        safe, reason = safe_destination(path, path)
        assert safe is False
        assert "identical" in reason

    def test_existing_destination_is_unsafe(self, tmp_path):
        src = tmp_path / "a.txt"
        dst = tmp_path / "b.txt"
        src.write_text("")
        dst.write_text("")
        safe, reason = safe_destination(src, dst)
        assert safe is False

    def test_valid_move_is_safe(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("")
        dst = tmp_path / "sub" / "a.txt"
        safe, reason = safe_destination(src, dst)
        assert safe is True


# ------------------------------------------------------------------
# validate_plan
# ------------------------------------------------------------------


class TestValidatePlan:
    def test_valid_plan_has_no_errors(self, downloads):
        _touch(downloads, "report.pdf")
        plan = {"Documents": ["report.pdf"]}
        errors = validate_plan(downloads, plan, ALLOWED_CATEGORIES)
        assert errors == []

    def test_duplicate_file_in_plan(self, downloads):
        _touch(downloads, "report.pdf")
        plan = {"Documents": ["report.pdf"], "Other": ["report.pdf"]}
        errors = validate_plan(downloads, plan, ALLOWED_CATEGORIES)
        assert any("Duplicate" in e for e in errors)

    def test_missing_file_in_plan(self, downloads):
        _touch(downloads, "actual.pdf")
        plan = {"Documents": []}  # actual.pdf not included
        errors = validate_plan(downloads, plan, ALLOWED_CATEGORIES)
        assert any("missing" in e.lower() for e in errors)

    def test_unknown_file_in_plan(self, downloads):
        plan = {"Documents": ["nonexistent.pdf"]}
        errors = validate_plan(downloads, plan, ALLOWED_CATEGORIES)
        assert any("does not exist" in e for e in errors)

    def test_invalid_category_rejected(self, downloads):
        _touch(downloads, "report.pdf")
        plan = {"MadeUp": ["report.pdf"]}
        errors = validate_plan(downloads, plan, ALLOWED_CATEGORIES)
        assert any("Unknown category" in e for e in errors)
