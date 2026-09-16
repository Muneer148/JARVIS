from __future__ import annotations

import json
import re
from typing import Any, Callable

from brain.prompts import SYSTEM_PROMPT
from brain.router import chat
from config.settings import MAX_TOOL_ROUNDS
from tools.base import ToolSpec

TOOL_PATTERN = re.compile(
    r"^TOOL_CALL:(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<args>\{.*\}))?\s*$",
    re.MULTILINE,
)


class Agent:
    def __init__(self, tools: dict[str, ToolSpec | Callable[..., Any]]) -> None:
        self.tools = tools
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt_with_tools()}
        ]

    def _system_prompt_with_tools(self) -> str:
        """Give the model the live registry contract instead of a stale tool list."""
        catalog: list[dict[str, Any]] = []
        for name, tool in sorted(self.tools.items()):
            if isinstance(tool, ToolSpec):
                catalog.append(tool.schema())
            else:
                catalog.append({
                    "name": name,
                    "description": "Legacy callable tool.",
                })
        return f"{SYSTEM_PROMPT}\n\nLIVE TOOL CATALOG:\n{json.dumps(catalog, indent=2, default=str)}"

    def _execute_tool(self, tool_name: str, raw_args: str | None) -> dict[str, Any] | Any:
        tool = self.tools.get(tool_name)
        if tool is None:
            return {"status": "error", "error": f"Unknown tool: {tool_name}"}

        args: dict[str, Any] = {}
        if raw_args:
            try:
                parsed = json.loads(raw_args)
            except json.JSONDecodeError as exc:
                return {"status": "error", "error": f"Invalid tool arguments: {exc.msg}"}
            if not isinstance(parsed, dict):
                return {"status": "error", "error": "Tool arguments must be a JSON object."}
            args = parsed

        try:
            if isinstance(tool, ToolSpec):
                return tool.execute(**args)
            return tool(**args)
        except TypeError as exc:
            return {"status": "error", "error": f"Invalid arguments for {tool_name}: {exc}"}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def run(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        for round_number in range(1, MAX_TOOL_ROUNDS + 1):
            response, provider = chat(self.messages, user_text)
            match = TOOL_PATTERN.search(response.strip())
            if not match:
                self.messages.append({"role": "assistant", "content": response})
                return response

            tool_name = match.group("name")
            result = self._execute_tool(tool_name, match.group("args"))
            self.messages.append({"role": "assistant", "content": response})
            tool_result = {
                "status": "tool_result",
                "round": round_number,
                "provider": provider,
                "tool": tool_name,
                "user_request": user_text,
                "result": result,
            }
            self.messages.append({"role": "user", "content": json.dumps(tool_result, default=str)})

        return "I reached the tool-operation limit for this request without producing a final answer."
