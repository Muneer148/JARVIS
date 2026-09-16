from __future__ import annotations

import os
import tempfile
import wave


def _record_wav(seconds: int = 7, sample_rate: int = 16_000) -> str:
    import sounddevice as sd

    frames = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(frames.tobytes())
    return path


def _whisper(path: str) -> str:
    from faster_whisper import WhisperModel

    model = WhisperModel(
        os.getenv("JARVIS_WHISPER_MODEL", "base"),
        device=os.getenv("JARVIS_WHISPER_DEVICE", "cpu"),
        compute_type=os.getenv("JARVIS_WHISPER_COMPUTE", "int8"),
    )
    segments, _ = model.transcribe(path, vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments).strip()


def listen(seconds: int = 7) -> dict[str, str]:
    path = ""
    try:
        path = _record_wav(seconds)
        text = _whisper(path)
        return {"status": "ok", "text": text}
    except Exception as exc:
        return {"status": "error", "text": "", "message": str(exc)}
    finally:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass


def transcribe(audio_path: str) -> dict[str, str]:
    try:
        return {"status": "ok", "text": _whisper(audio_path)}
    except Exception as exc:
        return {"status": "error", "text": "", "message": str(exc)}
