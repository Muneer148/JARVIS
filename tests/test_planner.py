from brain.planner import Agent


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
