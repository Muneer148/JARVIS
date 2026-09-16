"""Tests for tools/filesystem.py and safety/validator.py"""

from __future__ import annotations

from pathlib import Path

import pytest

from safety.validator import safe_destination, validate_plan
from tools.filesystem import (
    ALLOWED_CATEGORIES,
    _category_for,
    analyze_downloads,
    build_plan,
    execute_plan,
    organize_downloads,
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


class TestBuildPlan:
    def test_empty_directory_returns_empty_plan(self, downloads):
        assert build_plan(downloads) == {}

    def test_single_file_placed_correctly(self, downloads):
        _touch(downloads, "report.pdf")
        assert "report.pdf" in build_plan(downloads)["Documents"]

    def test_directories_excluded_from_plan(self, downloads):
        (downloads / "subfolder").mkdir()
        assert build_plan(downloads) == {}

    def test_multiple_categories(self, downloads):
        _touch(downloads, "photo.jpg")
        _touch(downloads, "song.mp3")
        _touch(downloads, "report.pdf")
        plan = build_plan(downloads)
        assert {"Images", "Audio", "Documents"}.issubset(plan)

    def test_all_plan_categories_are_allowed(self, downloads):
        _touch(downloads, "unknown.xyz")
        assert all(cat in ALLOWED_CATEGORIES for cat in build_plan(downloads))


class TestAnalyzeDownloads:
    def test_nonexistent_directory(self, tmp_path):
        assert analyze_downloads(tmp_path / "NoSuchFolder")["status"] == "error"

    def test_valid_directory(self, downloads):
        _touch(downloads, "file.pdf")
        _touch(downloads, "image.png")
        result = analyze_downloads(downloads)
        assert result["status"] == "ok"
        assert result["total_files"] == 2
        assert "Documents" in result["categories"]
        assert "Images" in result["categories"]

    def test_analysis_is_read_only(self, downloads):
        _touch(downloads, "file.pdf")
        analyze_downloads(downloads)
        assert (downloads / "file.pdf").exists()
        assert not (downloads / "Documents").exists()


class TestExecutePlan:
    def test_files_are_moved_and_verified(self, downloads):
        _touch(downloads, "report.pdf")
        result = execute_plan(downloads, {"Documents": ["report.pdf"]})
        assert result["status"] == "success"
        assert result["verified_count"] == 1
        assert (downloads / "Documents" / "report.pdf").exists()
        assert not (downloads / "report.pdf").exists()

    def test_empty_plan_succeeds(self, downloads):
        result = execute_plan(downloads, {})
        assert result["status"] == "success"
        assert result["moved_count"] == 0

    def test_missing_source_file_fails_validation(self, downloads):
        assert execute_plan(downloads, {"Documents": ["ghost.pdf"]})["status"] == "rejected"

    def test_unknown_category_fails_validation(self, downloads):
        _touch(downloads, "file.pdf")
        assert execute_plan(downloads, {"InvalidCategory": ["file.pdf"]})["status"] == "rejected"

    def test_destination_collision_is_rejected_without_overwrite(self, downloads):
        _touch(downloads, "report.pdf")
        destination = downloads / "Documents"
        destination.mkdir()
        (destination / "report.pdf").write_text("existing", encoding="utf-8")
        result = execute_plan(downloads, {"Documents": ["report.pdf"]})
        assert result["status"] == "rejected"
        assert (downloads / "report.pdf").read_text(encoding="utf-8") == ""
        assert (destination / "report.pdf").read_text(encoding="utf-8") == "existing"

    def test_incomplete_plan_is_rejected(self, downloads):
        _touch(downloads, "a.txt")
        _touch(downloads, "b.txt")
        result = execute_plan(downloads, {"Documents": ["a.txt"]})
        assert result["status"] == "rejected"
        assert any("File missing from plan: b.txt" in e for e in result["errors"])
        assert (downloads / "a.txt").exists()
        assert (downloads / "b.txt").exists()


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
        safe, _ = safe_destination(src, dst)
        assert safe is False

    def test_valid_move_is_safe(self, tmp_path):
        src = tmp_path / "a.txt"
        src.write_text("")
        safe, _ = safe_destination(src, tmp_path / "sub" / "a.txt")
        assert safe is True


class TestValidatePlan:
    def test_valid_plan_has_no_errors(self, downloads):
        _touch(downloads, "report.pdf")
        assert validate_plan(downloads, {"Documents": ["report.pdf"]}, ALLOWED_CATEGORIES) == []

    def test_duplicate_file_in_plan(self, downloads):
        _touch(downloads, "report.pdf")
        errors = validate_plan(downloads, {"Documents": ["report.pdf"], "Other": ["report.pdf"]}, ALLOWED_CATEGORIES)
        assert any("Duplicate" in e for e in errors)

    def test_missing_file_in_plan(self, downloads):
        _touch(downloads, "actual.pdf")
        errors = validate_plan(downloads, {"Documents": []}, ALLOWED_CATEGORIES)
        assert any("missing" in e.lower() for e in errors)

    def test_unknown_file_in_plan(self, downloads):
        errors = validate_plan(downloads, {"Documents": ["nonexistent.pdf"]}, ALLOWED_CATEGORIES)
        assert any("does not exist" in e for e in errors)

    def test_invalid_category_rejected(self, downloads):
        _touch(downloads, "report.pdf")
        errors = validate_plan(downloads, {"MadeUp": ["report.pdf"]}, ALLOWED_CATEGORIES)
        assert any("Unknown category" in e for e in errors)


class TestApprovalBoundary:
    def test_organize_downloads_has_no_embedded_prompt(self, downloads):
        """The tool must execute only after PermissionEngine authorization."""
        _touch(downloads, "notes.txt")
        result = organize_downloads(downloads)
        assert "success" in result
        assert (downloads / "Documents" / "notes.txt").exists()
