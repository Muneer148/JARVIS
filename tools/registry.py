from __future__ import annotations

from config.settings import DOWNLOADS_DIR
from tools.base import Permission, ToolSpec
from tools.diagnostics import project_health, resource_info
from tools.filesystem import analyze_downloads, organize_downloads
from tools.system import system_info
from tools.terminal import terminal


def make_registry() -> dict[str, ToolSpec]:
    """Build the canonical JARVIS tool registry.

    The registry deliberately contains metadata as well as handlers so the
    agent can later expose the same contract through MCP, APIs, or UI tools.
    """
    tools = [
        ToolSpec(
            "analyze_downloads",
            "Inspect the Downloads directory and produce an organization analysis without changing files.",
            lambda: analyze_downloads(DOWNLOADS_DIR),
            frozenset({Permission.READ}),
            risk_level="low",
        ),
        ToolSpec(
            "organize_downloads",
            "Organize files in the Downloads directory using the validated filesystem safety pipeline.",
            lambda: organize_downloads(DOWNLOADS_DIR),
            frozenset({Permission.READ, Permission.WRITE}),
            risk_level="medium",
            reversible=True,
            requires_approval=True,
        ),
        ToolSpec(
            "system_info",
            "Read basic operating-system and machine information.",
            system_info,
            frozenset({Permission.READ, Permission.SYSTEM}),
            risk_level="low",
        ),
        ToolSpec(
            "resource_info",
            "Read CPU, memory, and disk resource information.",
            resource_info,
            frozenset({Permission.READ, Permission.SYSTEM}),
            risk_level="low",
        ),
        ToolSpec(
            "project_health",
            "Check JARVIS project files, Git state, Python version, and the test suite.",
            project_health,
            frozenset({Permission.READ}),
            risk_level="low",
        ),
        ToolSpec(
            "terminal",
            "Run an approved terminal command when terminal execution is explicitly enabled.",
            terminal,
            frozenset({Permission.EXECUTE, Permission.SYSTEM}),
            risk_level="high",
            requires_approval=True,
        ),
    ]
    return {tool.name: tool for tool in tools}
