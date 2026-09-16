from __future__ import annotations

from brain.planner import Agent
from voice.speech_to_text import listen
from voice.text_to_speech import speak


class VoiceAssistant:
    """Local Windows voice loop around the existing JARVIS agent."""

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def run(self) -> None:
        print("Voice mode enabled. Speak after the listening prompt.")
        print("Say 'exit' or 'quit' to stop voice mode.")

        while True:
            try:
                print("\n[JARVIS listening...]")
                result = listen()
                if result["status"] != "ok":
                    print(f"JARVIS voice error: {result['message']}")
                    continue

                user_text = result["text"].strip()
                if not user_text:
                    continue

                print(f"You: {user_text}")
                if user_text.lower() in {"exit", "quit", "goodbye", "stop"}:
                    speak("Goodbye.")
                    print("JARVIS: Goodbye.")
                    break

                print("\n[JARVIS thinking...]\n")
                response = self.agent.run(user_text)
                print(f"JARVIS: {response}")
                speak(response)
            except (EOFError, KeyboardInterrupt):
                print("\nJARVIS: Goodbye.")
                break
            except Exception as exc:
                print(f"JARVIS: Runtime error: {exc}")
