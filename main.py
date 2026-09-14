from __future__ import annotations

from brain.planner import Agent
from tools.registry import make_registry


def main() -> None:
    print("=" * 48)
    print("JARVIS — Local Personal AI Agent")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 48)

    agent = Agent(make_registry())
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
