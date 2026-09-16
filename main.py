from __future__ import annotations

from brain.planner import Agent
from safety.permissions import PermissionEngine
from tools.registry import make_registry


def console_approval(tool, reason: str) -> bool:
    """Ask the human before a privileged tool is executed."""
    print(f"\n[JARVIS approval required]")
    print(f"Tool: {tool.name}")
    print(f"Risk: {tool.risk_level}")
    print(f"Permissions: {', '.join(sorted(permission.value for permission in tool.permissions))}")
    print(f"Reason: {reason}")
    answer = input("Allow this action? (yes/no): ").strip().lower()
    return answer in {"yes", "y"}


def main() -> None:
    print("=" * 48)
    print("JARVIS — Local Personal AI Agent")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 48)

    permission_engine = PermissionEngine(approval_callback=console_approval)
    agent = Agent(make_registry(), permission_engine=permission_engine)

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
