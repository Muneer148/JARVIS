from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from inspect import Parameter, signature
from typing import Any, Callable


class Permission(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass(frozen=True)
class ToolSpec:
    """Common contract for every JARVIS tool.

    Keeping metadata next to the callable lets native Python tools, MCP tools,
    API adapters, and future computer-control tools share one interface.
    """

    name: str
    description: str
    handler: Callable[..., Any]
    permissions: frozenset[Permission] = field(default_factory=lambda: frozenset({Permission.READ}))
    risk_level: str = "low"
    reversible: bool = False
    requires_approval: bool = False

    def execute(self, **kwargs: Any) -> Any:
        return self.handler(**kwargs)

    def schema(self) -> dict[str, Any]:
        """Return a small OpenAI/MCP-friendly description of the callable."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for name, parameter in signature(self.handler).parameters.items():
            if parameter.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
                continue
            properties[name] = {"type": "string"}
            if parameter.default is Parameter.empty:
                required.append(name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "permissions": sorted(permission.value for permission in self.permissions),
            "risk_level": self.risk_level,
            "reversible": self.reversible,
            "requires_approval": self.requires_approval,
        }
