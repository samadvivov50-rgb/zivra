from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from app.models import PermissionLevel, ToolCategory, ToolResult


@dataclass(slots=True)
class ToolDefinition:
    name: str
    category: ToolCategory
    permission_level: PermissionLevel
    description: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["category"] = self.category.value
        payload["permission_level"] = self.permission_level.value
        return payload


class BaseTool(ABC):
    definition: ToolDefinition

    @abstractmethod
    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        raise NotImplementedError
