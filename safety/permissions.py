from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tools.base import Permission, ToolSpec


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class PermissionEngine:
    """Central policy boundary for tool execution.

    The engine is deliberately conservative: read-only low-risk tools may run
    automatically, while write/execute/system operations remain approval-gated.
    A future UI can provide the approval callback without changing the policy.
    """

    AUTO_ALLOWED_RISKS = frozenset({"low"})
    APPROVAL_PERMISSIONS = frozenset({
        Permission.WRITE,
        Permission.EXECUTE,
        Permission.SYSTEM,
        Permission.NETWORK,
    })

    def __init__(self, *, approval_callback=None) -> None:
        self.approval_callback = approval_callback

    def evaluate(self, tool: ToolSpec) -> ApprovalDecision:
        if tool.requires_approval:
            return ApprovalDecision(False, True, f"{tool.name} requires approval")

        if tool.risk_level not in self.AUTO_ALLOWED_RISKS:
            return ApprovalDecision(False, True, f"{tool.name} has risk level '{tool.risk_level}'")

        if tool.permissions & self.APPROVAL_PERMISSIONS:
            return ApprovalDecision(False, True, f"{tool.name} requests privileged permissions")

        return ApprovalDecision(True, False, "policy allows automatic execution")

    def authorize(self, tool: ToolSpec) -> ApprovalDecision:
        decision = self.evaluate(tool)
        if not decision.requires_approval:
            return decision

        if self.approval_callback is None:
            return decision

        approved = bool(self.approval_callback(tool, decision.reason))
        if approved:
            return ApprovalDecision(True, False, "approved by user")
        return ApprovalDecision(False, True, "user denied approval")


def permissions_for(tool: ToolSpec) -> set[str]:
    return {permission.value for permission in tool.permissions}
