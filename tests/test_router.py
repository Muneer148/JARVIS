import brain.router as router


def test_auto_keeps_routine_requests_local(monkeypatch) -> None:
    monkeypatch.setattr(router, "BRAIN_MODE", "auto")
    monkeypatch.setattr(router.omniroute, "available", lambda: True)
    monkeypatch.setattr(router.nvidia, "available", lambda: True)
    monkeypatch.setattr(router.openrouter, "available", lambda: True)

    assert router.choose_provider("What is my system information?") == "local"


def test_auto_prefers_omniroute_for_complex_requests(monkeypatch) -> None:
    monkeypatch.setattr(router, "BRAIN_MODE", "auto")
    monkeypatch.setattr(router.omniroute, "available", lambda: True)
    monkeypatch.setattr(router.nvidia, "available", lambda: True)
    monkeypatch.setattr(router.openrouter, "available", lambda: True)

    assert router.choose_provider("Do a deep analysis of this architecture") == "omniroute"


def test_auto_falls_back_to_nvidia_when_omniroute_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(router, "BRAIN_MODE", "auto")
    monkeypatch.setattr(router.omniroute, "available", lambda: False)
    monkeypatch.setattr(router.nvidia, "available", lambda: True)
    monkeypatch.setattr(router.openrouter, "available", lambda: True)

    assert router.choose_provider("Analyze this code deeply and explain the architecture") == "nvidia"


def test_auto_falls_back_to_openrouter_when_other_gateways_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(router, "BRAIN_MODE", "auto")
    monkeypatch.setattr(router.omniroute, "available", lambda: False)
    monkeypatch.setattr(router.nvidia, "available", lambda: False)
    monkeypatch.setattr(router.openrouter, "available", lambda: True)

    assert router.choose_provider("Please reason deeply about this difficult design") == "openrouter"


def test_explicit_mode_is_respected(monkeypatch) -> None:
    monkeypatch.setattr(router, "BRAIN_MODE", "omniroute")
    monkeypatch.setattr(router.omniroute, "available", lambda: False)

    assert router.choose_provider("hello") == "omniroute"


def test_gateway_failure_returns_local_fallback(monkeypatch) -> None:
    monkeypatch.setattr(router, "BRAIN_MODE", "omniroute")
    monkeypatch.setattr(router.omniroute, "chat", lambda messages, model: (_ for _ in ()).throw(RuntimeError("gateway down")))
    monkeypatch.setattr(router.ollama, "chat", lambda messages, model: "local answer")

    response, provider = router.chat([{"role": "user", "content": "hello"}], "hello")

    assert response == "local answer"
    assert provider == "local-fallback"
