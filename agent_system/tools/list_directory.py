import os
from typing import Dict, Any
from ..core import Tool

class ListDirectoryTool(Tool):
    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "List files and directories in a given path. Use this to explore the file system or find specific files."

    def execute(self, path: str = ".") -> str:
        try:
            items = os.listdir(path)
            return "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to list. Defaults to current directory '.'"
                    }
                },
                "required": []
            }
        }
