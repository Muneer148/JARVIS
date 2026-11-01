from __future__ import annotations

from config.settings import DOWNLOADS_DIR
from tools.base import Permission, ToolSpec
from tools.browser import browse_url
from tools.diagnostics import project_health, resource_info
from tools.filesystem import analyze_downloads, organize_downloads
from tools.memory import forget_memory, list_memories, recall, remember
from tools.system import system_info
from tools.terminal import terminal


def make_registry() -> dict[str, ToolSpec]:
    """Build the canonical JARVIS tool registry."""
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
        ToolSpec(
            "remember",
            "Store a piece of information persistently for future recall. Args: text, category, tags.",
            remember,
            frozenset({Permission.READ, Permission.WRITE}),
            risk_level="low",
        ),
        ToolSpec(
            "recall",
            "Search JARVIS's persistent memory for stored facts relevant to a query. Args: query, limit.",
            recall,
            frozenset({Permission.READ}),
            risk_level="low",
        ),
        ToolSpec(
            "forget_memory",
            "Permanently delete a stored memory by numeric id. Use recall first to identify the id.",
            forget_memory,
            frozenset({Permission.WRITE}),
            risk_level="high",
            reversible=False,
            requires_approval=True,
        ),
        ToolSpec(
            "list_memories",
            "List stored memories, optionally filtered by category. Args: category.",
            list_memories,
            frozenset({Permission.READ}),
            risk_level="low",
        ),
        ToolSpec(
            "browse_url",
            "Fetch a public web page and return readable text, title, and links. Public http/https only; no JavaScript rendering.",
            browse_url,
            frozenset({Permission.NETWORK}),
            risk_level="low",
        ),
    ]
    return {tool.name: tool for tool in tools}
