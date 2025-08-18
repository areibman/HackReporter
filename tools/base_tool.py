from __future__ import annotations

from typing import Any


class BaseTool:
    """Minimal no-op BaseTool to keep existing tool classes working without CrewAI."""

    name: str = "base_tool"
    description: str = ""
    args_schema: Any | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def _run(self, *args: Any, **kwargs: Any) -> Any:  # To be implemented by subclasses
        raise NotImplementedError

