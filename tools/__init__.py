# Lazy-import pattern to keep cold-start times low.  We only load the heavy
# sub-modules if/when their classes are first requested.

from importlib import import_module
from types import ModuleType
from typing import Any, Dict

_lazy_map: Dict[str, str] = {
    "GeminiVideoTool": ".gemini_video_tool",
    "TwitterSearchTool": ".twitter_tool",
    "TypefullyTool": ".typefully_tool",
    "FileReaderTool": ".file_reader_tool",
}

__all__ = list(_lazy_map.keys())


def __getattr__(name: str) -> Any:  # noqa: D401 (simple function)
    """Dynamically import sub-modules on first attribute access."""
    if name not in _lazy_map:
        raise AttributeError(f"module 'tools' has no attribute '{name}'")

    module_path = _lazy_map[name]
    module: ModuleType = import_module(module_path, package=__name__)
    attr = getattr(module, name)
    globals()[name] = attr  # cache for future access
    return attr
