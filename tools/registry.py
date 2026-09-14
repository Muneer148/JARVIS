from __future__ import annotations

from pathlib import Path
from typing import Callable

from config.settings import DOWNLOADS_DIR
from tools.filesystem import analyze_downloads, organize_downloads
from tools.system import system_info
from tools.terminal import terminal


def make_registry() -> dict[str, Callable]:
    return {
        "analyze_downloads": lambda: analyze_downloads(DOWNLOADS_DIR),
        "organize_downloads": lambda: organize_downloads(DOWNLOADS_DIR),
        "system_info": system_info,
        "terminal": terminal,
    }
