from __future__ import annotations

import os


def speak(text: str) -> dict[str, str]:
    """Speak text locally using Windows SAPI; no cloud service required."""
    try:
        import subprocess

        safe_text = text.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Rate={int(os.getenv('JARVIS_TTS_RATE', '0'))}; "
            f"$s.Speak('{safe_text}')"
        )
        subprocess.run(["powershell.exe", "-NoProfile", "-Command", script], check=True)
        return {"status": "ok", "message": "spoken"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
