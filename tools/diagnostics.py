from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _windows_memory() -> dict[str, int] | None:
    if platform.system() != "Windows":
        return None

    import ctypes

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return {
        "total_bytes": int(status.ullTotalPhys),
        "available_bytes": int(status.ullAvailPhys),
        "used_percent": int(status.dwMemoryLoad),
    }


def resource_info() -> dict[str, Any]:
    """Return read-only CPU, memory, and disk information."""
    disk = shutil.disk_usage(PROJECT_ROOT)
    memory = _windows_memory()
    result: dict[str, Any] = {
        "status": "ok",
        "cpu_count_logical": os.cpu_count(),
        "disk": {
            "path": str(PROJECT_ROOT.anchor or PROJECT_ROOT),
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        },
    }
    result["memory"] = memory if memory is not None else {"status": "unavailable"}
    return result


def _run(command: list[str], timeout: float = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"available": False, "error": f"Command not found: {command[0]}"}
    except subprocess.TimeoutExpired:
        return {"available": False, "error": f"Command timed out: {' '.join(command)}"}
    return {
        "available": True,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip()[-4000:],
        "stderr": completed.stderr.strip()[-4000:],
    }


def project_health() -> dict[str, Any]:
    """Run read-only checks against the current JARVIS checkout."""
    required = [
        "main.py",
        "brain/router.py",
        "brain/planner.py",
        "tools/registry.py",
        "config/settings.py",
        "tests",
    ]
    paths = {item: (PROJECT_ROOT / item).exists() for item in required}
    git = _run(["git", "status", "--short", "--branch"], timeout=10)
    tests = _run([sys.executable, "-m", "pytest", "-q"], timeout=90)
    healthy = all(paths.values()) and git.get("available", False) and tests.get("returncode") == 0
    return {
        "status": "healthy" if healthy else "attention_required",
        "project_root": str(PROJECT_ROOT),
        "required_paths": paths,
        "git": git,
        "tests": tests,
        "python": sys.version,
    }
