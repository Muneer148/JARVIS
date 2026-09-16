from __future__ import annotations

import sys

from brain.planner import Agent
from tools.registry import make_registry


def main() -> None:
    print("=" * 48)
    print("JARVIS — Local Personal AI Agent")
    print("1. Text mode")
    print("2. Voice mode")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 48)

    agent = Agent(make_registry())
    mode = input("Select mode [1/2]: ").strip()

    if mode == "2":
        try:
            from voice.assistant import VoiceAssistant
            VoiceAssistant(agent).run()
        except ImportError as exc:
            print(f"JARVIS: Voice dependencies are missing: {exc}")
            print("Install requirements.txt and try again.")
        return

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJARVIS: Goodbye.")
            break

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            print("JARVIS: Goodbye.")
            break

        try:
            print("\n[JARVIS thinking...]\n")
            print(f"JARVIS: {agent.run(user_text)}")
        except Exception as exc:
            print(f"JARVIS: Runtime error: {exc}")


if __name__ == "__main__":
    main()
