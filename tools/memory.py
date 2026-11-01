"""
tools/memory.py
================
Persistent long-term memory for JARVIS.

Design decisions (aligned with the JARVIS project requirements):
  - Standard library only. No vector DB, no embeddings, no extra dependencies.
  - Local-first: single JSON file on disk, readable and recoverable by a human.
  - Safe by default: JARVIS stores nothing without an explicit ``remember`` call.
  - Atomic writes: uses a temp-file-then-replace strategy so a crash during a
    write never leaves a corrupt memory file.
  - Thread-safe: a module-level lock protects concurrent access if JARVIS is
    ever extended to handle parallel tool rounds.
  - Provider-agnostic: pure storage/retrieval — completely independent of which
    LLM backend is active (Ollama, OmniRoute, NVIDIA, etc.).

Storage format (``data/memory.json``):
    {
      "entries": [
        {
          "id": 1,
          "text": "User prefers dark-roast coffee",
          "category": "preferences",
          "tags": ["coffee"],
          "created_at": "2026-09-17T10:22:31+00:00"
        }
      ],
      "next_id": 2
    }

Recall strategy:
    Simple, transparent keyword scoring: count how many query words appear in
    the entry's text, category, and tags. Fast, inspectable, zero dependencies,
    and easily replaceable with an embedding scorer later without touching the
    tool interface.

Tool registration (tools/registry.py):
    Four ToolSpec entries, all READ-only, risk_level="low":
        remember       -> remember(text, category="general", tags="")
        recall         -> recall(query, limit="5")
        forget_memory  -> forget_memory(id)
        list_memories  -> list_memories(category="")

    These follow the ToolSpec.execute(**kwargs) convention exactly: handler
    arguments must match what the model passes in the TOOL_CALL JSON payload.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MEMORY_PATH = Path(
    os.environ.get("JARVIS_MEMORY_PATH", "data/memory.json")
)
_lock = threading.Lock()


@dataclass
class _Entry:
    id: int
    text: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _MemoryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[_Entry] = []
        self._next_id = 1
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._entries = [_Entry(**e) for e in raw.get("entries", [])]
            self._next_id = raw.get("next_id", len(self._entries) + 1)
        except (json.JSONDecodeError, TypeError, OSError):
            # Corrupt or unreadable: move the bad file aside and start clean.
            backup = self._path.with_suffix(".corrupt.json")
            try:
                self._path.replace(backup)
            except OSError:
                pass
            self._entries = []
            self._next_id = 1

    def _save(self) -> None:
        payload = {
            "entries": [e.to_dict() for e in self._entries],
            "next_id": self._next_id,
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)  # atomic on both POSIX and Windows

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def remember(self, text: str, category: str, tags: list[str]) -> _Entry:
        if not text.strip():
            raise ValueError("Cannot store an empty memory")
        with _lock:
            entry = _Entry(id=self._next_id, text=text.strip(), category=category or "general", tags=tags)
            self._entries.append(entry)
            self._next_id += 1
            self._save()
            return entry

    def recall(self, query: str, limit: int) -> list[_Entry]:
        if not query.strip():
            return []
        words = [w.lower() for w in query.split() if w]
        scored: list[tuple[int, _Entry]] = []
        for entry in self._entries:
            haystack = " ".join([entry.text, entry.category, *entry.tags]).lower()
            score = sum(1 for w in words if w in haystack)
            if score:
                scored.append((score, entry))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def forget(self, entry_id: int) -> bool:
        with _lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e.id != entry_id]
            if len(self._entries) != before:
                self._save()
                return True
            return False

    def list_all(self, category: str) -> list[_Entry]:
        if category:
            return [e for e in self._entries if e.category == category]
        return list(self._entries)


# Module-level singleton so the whole process shares one store.
_store: _MemoryStore | None = None


def _get_store() -> _MemoryStore:
    global _store
    if _store is None:
        _store = _MemoryStore(_MEMORY_PATH)
    return _store


# ------------------------------------------------------------------
# Tool handlers — signatures must exactly match the keyword args the
# model passes in the TOOL_CALL JSON payload, because ToolSpec.execute
# calls handler(**kwargs) directly.
# ------------------------------------------------------------------


def remember(
    text: str,
    category: str = "general",
    tags: str = "",
) -> dict[str, Any]:
    """Store a piece of information for later recall.

    Args:
        text:     The fact or note to remember.
        category: A label to group memories (e.g. "preferences", "people",
                  "schedule"). Defaults to "general".
        tags:     Optional comma-separated keywords for faster recall.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    try:
        entry = _get_store().remember(text=text, category=category, tags=tag_list)
        return {
            "status": "ok",
            "id": entry.id,
            "stored": entry.text,
            "category": entry.category,
        }
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}


def recall(query: str, limit: str = "5") -> dict[str, Any]:
    """Search stored memories by keyword relevance.

    Args:
        query: Words or phrases to search for.
        limit: Maximum number of results to return (default 5).
    """
    try:
        n = max(1, int(limit))
    except (ValueError, TypeError):
        n = 5
    results = _get_store().recall(query=query, limit=n)
    return {
        "status": "ok",
        "count": len(results),
        "results": [e.to_dict() for e in results],
    }


def forget_memory(id: str) -> dict[str, Any]:
    """Delete a stored memory by its numeric id.

    Args:
        id: The numeric id of the memory entry to delete.
    """
    try:
        entry_id = int(id)
    except (ValueError, TypeError):
        return {"status": "error", "message": "'id' must be a number"}
    removed = _get_store().forget(entry_id)
    return {"status": "ok" if removed else "not_found", "id": entry_id}


def list_memories(category: str = "") -> dict[str, Any]:
    """List stored memories, optionally filtered by category.

    Args:
        category: Return only memories in this category. Leave blank for all.
    """
    results = _get_store().list_all(category=category.strip())
    return {
        "status": "ok",
        "count": len(results),
        "results": [e.to_dict() for e in results],
    }
