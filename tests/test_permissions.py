from safety.permissions import PermissionEngine
from tools.base import Permission, ToolSpec


def test_read_only_low_risk_tool_is_auto_allowed() -> None:
    tool = ToolSpec(
        "status",
        "Read status",
        lambda: {"status": "ok"},
        frozenset({Permission.READ}),
    )
    decision = PermissionEngine().authorize(tool)
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_write_tool_is_blocked_without_approval() -> None:
    tool = ToolSpec(
        "write",
        "Write data",
        lambda: None,
        frozenset({Permission.WRITE}),
        risk_level="medium",
        requires_approval=True,
    )
    decision = PermissionEngine().authorize(tool)
    assert decision.allowed is False
    assert decision.requires_approval is True


def test_approval_callback_can_authorize_privileged_tool() -> None:
    tool = ToolSpec(
        "terminal",
        "Run command",
        lambda: "ok",
        frozenset({Permission.EXECUTE}),
        risk_level="high",
        requires_approval=True,
    )
    engine = PermissionEngine(approval_callback=lambda _tool, _reason: True)
    decision = engine.authorize(tool)
    assert decision.allowed is True
    assert decision.requires_approval is False
