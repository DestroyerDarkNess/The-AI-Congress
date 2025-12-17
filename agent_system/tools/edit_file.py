import os
from typing import Dict, Any, Optional
from ..core import Tool

class EditFileTool(Tool):
    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Smartly edit a file by replacing a unique block of text with new content. Use this for large files to avoid rewriting the whole file."

    def execute(self, path: str, target_text: str, replacement_text: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist."

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            # Normalize line endings for comparison (optional but recommended)
            # content_normalized = content.replace('\r\n', '\n')
            # target_normalized = target_text.replace('\r\n', '\n')
            
            # Check for occurrences
            count = content.count(target_text)
            
            if count == 0:
                # Try to be helpful: check if it's an indentation issue or whitespace
                # For now, just return a clear error
                return (
                    f"Error: 'target_text' not found in {path}. "
                    "Ensure you are using the EXACT text from the file, including whitespace. "
                    "Use read_file to verify the content first."
                )
            
            if count > 1:
                return (
                    f"Error: 'target_text' found {count} times in {path}. "
                    "Please provide a more unique block of text (more context) to identify the section to replace."
                )

            # Perform replacement
            new_content = content.replace(target_text, replacement_text)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return f"Successfully edited {path}."

        except Exception as e:
            return f"Error editing file: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to edit."
                    },
                    "target_text": {
                        "type": "string",
                        "description": "The exact block of text to replace. Must be unique in the file."
                    },
                    "replacement_text": {
                        "type": "string",
                        "description": "The new text to insert in place of target_text."
                    }
                },
                "required": ["path", "target_text", "replacement_text"]
            }
        }
