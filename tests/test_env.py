from pathlib import Path

from config.env import load_env


def test_load_env_reads_local_values_without_overwriting_existing(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "JARVIS_TEST_VALUE=from-file\n"
        "JARVIS_EXISTING=from-file\n"
        "export JARVIS_QUOTED=\"quoted value\"\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("JARVIS_EXISTING", "from-process")

    load_env(env_file)

    assert __import__("os").environ["JARVIS_TEST_VALUE"] == "from-file"
    assert __import__("os").environ["JARVIS_EXISTING"] == "from-process"
    assert __import__("os").environ["JARVIS_QUOTED"] == "quoted value"
