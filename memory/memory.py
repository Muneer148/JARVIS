from __future__ import annotations

from pathlib import Path

from memory.database import MemoryDB


class Memory:
    def __init__(self, path: Path) -> None:
        self.db = MemoryDB(path)

    def remember(self, content: str) -> None:
        self.db.add(content)

    def recall(self, limit: int = 10) -> list[str]:
        return self.db.recent(limit)
