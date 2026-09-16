from brain.planner import Agent
from tools.base import Permission, ToolSpec


def test_structured_tool_call_passes_json_arguments(monkeypatch) -> None:
    responses = iter([
        ('TOOL_CALL:echo:{"value":"hello"}', 'local'),
        ('The verified result is hello.', 'local'),
    ])

    monkeypatch.setattr("brain.planner.chat", lambda messages, user_text: next(responses))

    agent = Agent({"echo": lambda value: {"status": "ok", "value": value}})
    assert agent.run("echo hello") == "The verified result is hello."


def test_tool_error_becomes_structured_result(monkeypatch) -> None:
    responses = iter([
        ('TOOL_CALL:missing', 'local'),
        ('The requested tool was unavailable.', 'local'),
    ])

    monkeypatch.setattr("brain.planner.chat", lambda messages, user_text: next(responses))

    agent = Agent({})
    assert agent.run("use the missing tool") == "The requested tool was unavailable."


def test_agent_supports_tool_specs(monkeypatch) -> None:
    responses = iter([
        ('TOOL_CALL:echo:{"value":"hello"}', 'local'),
        ('done', 'local'),
    ])
    monkeypatch.setattr("brain.planner.chat", lambda messages, user_text: next(responses))

    tool = ToolSpec(
        name="echo",
        description="Return the supplied value.",
        handler=lambda value: {"status": "ok", "value": value},
        permissions=frozenset({Permission.READ}),
    )
    agent = Agent({"echo": tool})

    assert agent.run("echo hello") == "done"


def test_tool_spec_exposes_machine_readable_metadata() -> None:
    tool = ToolSpec(
        name="dangerous",
        description="Example tool.",
        handler=lambda value: value,
        permissions=frozenset({Permission.EXECUTE}),
        risk_level="high",
        requires_approval=True,
    )

    schema = tool.schema()
    assert schema["name"] == "dangerous"
    assert schema["input_schema"]["required"] == ["value"]
    assert schema["permissions"] == ["execute"]
    assert schema["risk_level"] == "high"
    assert schema["requires_approval"] is True
