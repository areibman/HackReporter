from typing import TYPE_CHECKING
import importlib

__all__ = ['GeminiVideoTool', 'TwitterSearchTool', 'TypefullyTool', 'FileReaderTool']

# Provide type hints for static analyzers without incurring import cost at runtime
if TYPE_CHECKING:
    from .gemini_video_tool import GeminiVideoTool  # noqa: F401
    from .twitter_tool import TwitterSearchTool  # noqa: F401
    from .typefully_tool import TypefullyTool  # noqa: F401
    from .file_reader_tool import FileReaderTool  # noqa: F401


def __getattr__(name: str):
    """Lazily import tool classes on first attribute access."""
    if name == 'GeminiVideoTool':
        module = importlib.import_module('.gemini_video_tool', __name__)
        return module.GeminiVideoTool
    if name == 'TwitterSearchTool':
        module = importlib.import_module('.twitter_tool', __name__)
        return module.TwitterSearchTool
    if name == 'TypefullyTool':
        module = importlib.import_module('.typefully_tool', __name__)
        return module.TypefullyTool
    if name == 'FileReaderTool':
        module = importlib.import_module('.file_reader_tool', __name__)
        return module.FileReaderTool
    raise AttributeError(f"module 'tools' has no attribute {name!r}")


def __dir__():
    return sorted(__all__)
