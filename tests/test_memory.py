"""Tests for tools/memory.py"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

import tools.memory as memory_module
from tools.memory import (
    _MemoryStore,
    forget_memory,
    list_memories,
    recall,
    remember,
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path):
    """Point the module singleton at a fresh temp store for every test."""
    path = tmp_path / "memory.json"
    memory_module._store = _MemoryStore(path)
    yield
    memory_module._store = None


# ------------------------------------------------------------------
# _MemoryStore unit tests
# ------------------------------------------------------------------


class TestMemoryStore:
    def test_remember_stores_and_persists(self, tmp_path):
        path = tmp_path / "mem.json"
        store = _MemoryStore(path)
        entry = store.remember("User's dog is named Max", "people", ["dog"])
        assert entry.id == 1
        assert path.exists()

        reloaded = _MemoryStore(path)
        assert len(reloaded.list_all("")) == 1
        assert reloaded.list_all("")[0].text == "User's dog is named Max"

    def test_remember_rejects_empty_text(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        with pytest.raises(ValueError):
            store.remember("   ", "general", [])

    def test_ids_auto_increment(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        a = store.remember("fact a", "general", [])
        b = store.remember("fact b", "general", [])
        assert b.id == a.id + 1

    def test_recall_scores_by_word_overlap(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        store.remember("User's dog is named Max", "people", [])
        store.remember("User likes dark roast coffee", "preferences", [])
        store.remember("Weekly standup every Monday", "schedule", [])

        results = store.recall("dog", 5)
        assert len(results) == 1
        assert "Max" in results[0].text

    def test_recall_returns_most_relevant_first(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        # "hiking hiking hiking" matches "hiking" 3 times; "cycling" matches 0 times
        # so a hiking query must rank the first entry higher than the second.
        store.remember("Loves hiking hiking hiking in the mountains", "hobbies", ["hiking"])
        store.remember("Enjoys cycling on weekdays", "hobbies", [])
        results = store.recall("hiking", 5)
        assert len(results) >= 1
        assert "hiking" in results[0].text

    def test_recall_empty_query_returns_nothing(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        store.remember("Something memorable", "general", [])
        assert store.recall("", 5) == []

    def test_recall_respects_limit(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        for i in range(10):
            store.remember(f"fact number {i}", "general", [])
        results = store.recall("fact", 3)
        assert len(results) <= 3

    def test_forget_removes_entry(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        entry = store.remember("Temporary", "general", [])
        assert store.forget(entry.id) is True
        assert store.list_all("") == []

    def test_forget_nonexistent_returns_false(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        assert store.forget(999) is False

    def test_list_filters_by_category(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        store.remember("fact A", "people", [])
        store.remember("fact B", "schedule", [])
        assert len(store.list_all("people")) == 1
        assert len(store.list_all("")) == 2

    def test_corrupt_file_recovers_gracefully(self, tmp_path):
        path = tmp_path / "mem.json"
        path.write_text("{not valid json", encoding="utf-8")
        store = _MemoryStore(path)
        assert store.list_all("") == []
        assert (tmp_path / "mem.corrupt.json").exists()

    def test_atomic_write_does_not_leave_tmp_file(self, tmp_path):
        store = _MemoryStore(tmp_path / "m.json")
        store.remember("test", "general", [])
        tmp_file = tmp_path / "m.tmp"
        assert not tmp_file.exists()

    def test_survives_restart(self, tmp_path):
        path = tmp_path / "m.json"
        s1 = _MemoryStore(path)
        s1.remember("persistent fact", "notes", ["important"])

        s2 = _MemoryStore(path)
        results = s2.recall("persistent", 5)
        assert len(results) == 1
        assert results[0].text == "persistent fact"


# ------------------------------------------------------------------
# Tool handler tests (exercise the public API the Agent calls)
# ------------------------------------------------------------------


class TestRemember:
    def test_basic_remember(self):
        result = remember(text="Loves hiking")
        assert result["status"] == "ok"
        assert result["id"] == 1
        assert result["stored"] == "Loves hiking"

    def test_remember_with_category_and_tags(self):
        result = remember(text="Enjoys hiking", category="hobbies", tags="hiking,outdoors")
        assert result["status"] == "ok"
        assert result["category"] == "hobbies"

    def test_remember_strips_whitespace(self):
        result = remember(text="  some fact  ")
        assert result["stored"] == "some fact"

    def test_remember_empty_text_returns_error(self):
        result = remember(text="")
        assert result["status"] == "error"

    def test_remember_whitespace_only_returns_error(self):
        result = remember(text="   ")
        assert result["status"] == "error"


class TestRecall:
    def test_recall_finds_stored_fact(self):
        remember(text="Favourite editor is Neovim", category="preferences")
        result = recall(query="editor")
        assert result["status"] == "ok"
        assert result["count"] == 1
        assert "Neovim" in result["results"][0]["text"]

    def test_recall_empty_query_returns_nothing(self):
        remember(text="Something")
        result = recall(query="")
        assert result["count"] == 0

    def test_recall_respects_limit_argument(self):
        for i in range(10):
            remember(text=f"important fact {i}")
        result = recall(query="important", limit="3")
        assert result["count"] <= 3

    def test_recall_invalid_limit_defaults_to_5(self):
        for i in range(10):
            remember(text=f"interesting item {i}")
        result = recall(query="interesting", limit="not_a_number")
        assert result["count"] <= 5

    def test_recall_no_match_returns_empty(self):
        remember(text="User likes coffee")
        result = recall(query="pizza")
        assert result["count"] == 0


class TestForgetMemory:
    def test_forget_removes_stored_entry(self):
        r = remember(text="Temporary note")
        entry_id = r["id"]
        result = forget_memory(id=str(entry_id))
        assert result["status"] == "ok"

        verify = recall(query="Temporary note")
        assert verify["count"] == 0

    def test_forget_nonexistent_id_returns_not_found(self):
        result = forget_memory(id="9999")
        assert result["status"] == "not_found"

    def test_forget_non_numeric_id_returns_error(self):
        result = forget_memory(id="abc")
        assert result["status"] == "error"


class TestListMemories:
    def test_list_all(self):
        remember(text="fact 1", category="notes")
        remember(text="fact 2", category="people")
        result = list_memories()
        assert result["count"] == 2

    def test_list_filtered_by_category(self):
        remember(text="fact 1", category="notes")
        remember(text="fact 2", category="people")
        result = list_memories(category="notes")
        assert result["count"] == 1
        assert result["results"][0]["category"] == "notes"

    def test_list_empty_store(self):
        result = list_memories()
        assert result["count"] == 0
        assert result["results"] == []
