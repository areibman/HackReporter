from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
from pathlib import Path


class FileReaderToolInput(BaseModel):
    """Input schema for FileReaderTool."""
    file_path: str = Field(
        description="Path to the file to read"
    )


class FileReaderTool(BaseTool):
    name: str = "file_reader"
    description: str = (
        "Read the contents of a file. "
        "Useful for reading JSON files, text files, or any other file content."
    )
    args_schema: Type[BaseModel] = FileReaderToolInput

    def _run(self, file_path: str) -> str:
        """
        Read the contents of a file.

        Args:
            file_path: Path to the file to read

        Returns:
            The contents of the file as a string
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return f"Error: File '{file_path}' does not exist"

            if not path.is_file():
                return f"Error: '{file_path}' is not a file"

            # Read the file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # If it's a JSON file, try to pretty print it
            if path.suffix.lower() == '.json':
                try:
                    data = json.loads(content)
                    return json.dumps(data, indent=2)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return raw content
                    pass

            return content

        except Exception as e:
            return f"Error reading file: {str(e)}"
