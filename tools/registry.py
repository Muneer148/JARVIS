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
    """Build the canonical JARVIS tool registry.

    The registry deliberately contains metadata as well as handlers so the
    agent can later expose the same contract through MCP, APIs, or UI tools.
    """
    tools = [
        # ── Filesystem ────────────────────────────────────────────────
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
        # ── System diagnostics ────────────────────────────────────────
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
        # ── Terminal ──────────────────────────────────────────────────
        ToolSpec(
            "terminal",
            "Run an approved terminal command when terminal execution is explicitly enabled.",
            terminal,
            frozenset({Permission.EXECUTE, Permission.SYSTEM}),
            risk_level="high",
            requires_approval=True,
        ),
        # ── Memory ───────────────────────────────────────────────────
        ToolSpec(
            "remember",
            (
                "Store a piece of information persistently for future recall. "
                "Use this for facts the user explicitly wants JARVIS to remember: "
                "preferences, names, schedules, notes. "
                "Args: text (required), category (optional, e.g. 'preferences'), "
                "tags (optional, comma-separated keywords)."
            ),
            remember,
            frozenset({Permission.READ, Permission.WRITE}),
            risk_level="low",
        ),
        ToolSpec(
            "recall",
            (
                "Search JARVIS's persistent memory for stored facts relevant to a query. "
                "Returns the most relevant entries scored by keyword overlap. "
                "Args: query (required), limit (optional, default 5)."
            ),
            recall,
            frozenset({Permission.READ}),
            risk_level="low",
        ),
        ToolSpec(
            "forget_memory",
            (
                "Delete a stored memory by its numeric id. "
                "Use recall first to find the id. "
                "Args: id (required, the numeric id from a recall or list_memories result)."
            ),
            forget_memory,
            frozenset({Permission.READ, Permission.WRITE}),
            risk_level="low",
        ),
        ToolSpec(
            "list_memories",
            (
                "List stored memories, optionally filtered by category. "
                "Args: category (optional — leave empty to list all memories)."
            ),
            list_memories,
            frozenset({Permission.READ}),
            risk_level="low",
        ),
        # ── Browser ──────────────────────────────────────────────────
        ToolSpec(
            "browse_url",
            (
                "Fetch a public web page and return its readable text, title, and links. "
                "Use this to look up current information, read articles, or verify facts. "
                "Only public http/https URLs are permitted; local services are blocked. "
                "Does not render JavaScript — some dynamic content may be absent. "
                "Args: url (required, full URL including https://)."
            ),
            browse_url,
            frozenset({Permission.NETWORK}),
            risk_level="low",
        ),
    ]
    return {tool.name: tool for tool in tools}
