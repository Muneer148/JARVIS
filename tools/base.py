from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from inspect import Parameter, signature
from typing import Any, Callable, get_args, get_origin, get_type_hints


class Permission(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    SYSTEM = "system"


def _json_type(annotation: Any) -> str:
    """Map common Python annotations to JSON Schema primitive types."""
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        if origin in (list, tuple, set):
            return "array"
        if origin is dict:
            return "object"
        if args:
            non_none = [arg for arg in args if arg is not type(None)]
            if len(non_none) == 1:
                return _json_type(non_none[0])
    if annotation in (int,):
        return "integer"
    if annotation in (float,):
        return "number"
    if annotation in (bool,):
        return "boolean"
    return "string"


@dataclass(frozen=True)
class ToolSpec:
    """Common contract for every JARVIS tool."""

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
        """Return an OpenAI/MCP-friendly JSON Schema for the callable."""
        properties: dict[str, Any] = {}
        required: list[str] = []
        try:
            hints = get_type_hints(self.handler)
        except (NameError, TypeError):
            hints = {}

        for name, parameter in signature(self.handler).parameters.items():
            if parameter.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
                continue
            annotation = hints.get(name, parameter.annotation)
            property_schema: dict[str, Any] = {"type": _json_type(annotation)}
            if parameter.default is not Parameter.empty:
                property_schema["default"] = parameter.default
            properties[name] = property_schema
            if parameter.default is Parameter.empty:
                required.append(name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            "permissions": sorted(permission.value for permission in self.permissions),
            "risk_level": self.risk_level,
            "reversible": self.reversible,
            "requires_approval": self.requires_approval,
        }
