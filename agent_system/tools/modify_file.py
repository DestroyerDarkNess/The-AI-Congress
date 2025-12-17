import os
from typing import Dict, Any
from ..core import Tool

class ModifyFileTool(Tool):
    @property
    def name(self) -> str:
        return "modify_file"

    @property
    def description(self) -> str:
        return "Write or overwrite content to a file."

    def execute(self, path: str, content: str) -> str:
        try:
            # Create parent directories if they don't exist
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
                
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to write to."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write."
                    }
                },
                "required": ["path", "content"]
            }
        }
