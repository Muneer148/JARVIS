from __future__ import annotations

import re
from typing import Callable, Any

from brain.ollama import chat
from brain.prompts import SYSTEM_PROMPT
from config.settings import MAX_TOOL_ROUNDS, MODEL

TOOL_PATTERN = re.compile(r"^TOOL_CALL:([A-Za-z_][A-Za-z0-9_]*)\s*$", re.MULTILINE)


class Agent:
    def __init__(self, tools: dict[str, Callable[..., Any]]) -> None:
        self.tools = tools
        self.messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def run(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        for _ in range(MAX_TOOL_ROUNDS):
            response = chat(self.messages, MODEL)
            match = TOOL_PATTERN.search(response.strip())
            if not match:
                self.messages.append({"role": "assistant", "content": response})
                return response

            tool_name = match.group(1)
            tool = self.tools.get(tool_name)
            if tool is None:
                result = {"status": "error", "error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    result = tool()
                except TypeError:
                    result = {"status": "error", "error": "Tool requires arguments that were not provided by the current protocol."}
                except Exception as exc:
                    result = {"status": "error", "error": str(exc)}

            self.messages.append({"role": "assistant", "content": response})
            tool_result = f"Tool `{tool_name}` result for the user's request `{user_text}`:\n{result}"
            self.messages.append({"role": "user", "content": tool_result})

        return "I reached the tool-operation limit for this request without producing a final answer."
