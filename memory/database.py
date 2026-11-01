from __future__ import annotations

import sqlite3
from pathlib import Path


class MemoryDB:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        self.connection.commit()

    def add(self, content: str) -> None:
        self.connection.execute("INSERT INTO memories(content) VALUES (?)", (content,))
        self.connection.commit()

    def recent(self, limit: int = 10) -> list[str]:
        rows = self.connection.execute("SELECT content FROM memories ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [row[0] for row in rows]
