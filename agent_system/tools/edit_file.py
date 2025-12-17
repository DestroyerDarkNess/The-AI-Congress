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

    def execute(self, path: str, target_text: str, replacement_text: str, regex: bool = False, case_insensitive: bool = False, replace_all: bool = False) -> str:
        try:
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist."

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            import re
            
            flags = 0
            if case_insensitive:
                flags |= re.IGNORECASE
            
            if regex:
                pattern = target_text
            else:
                pattern = re.escape(target_text)
            
            # Check for occurrences
            matches = list(re.finditer(pattern, content, flags=flags))
            count = len(matches)
            
            if count == 0:
                return (
                    f"Error: 'target_text' not found in {path}. "
                    "Ensure you are using the EXACT text from the file, including whitespace. "
                    "Use read_file to verify the content first."
                )
            
            if count > 1 and not replace_all:
                return (
                    f"Error: 'target_text' found {count} times in {path}. "
                    "Please provide a more unique block of text (more context) to identify the section to replace, "
                    "or set replace_all=True to replace all occurrences."
                )

            # Perform replacement
            # If replace_all is True, re.sub replaces all.
            # If replace_all is False, we already checked count == 1, so re.sub is fine (it replaces all, which is just 1).
            # However, re.sub might be risky if we only want to replace the *first* one but count > 1 (which we blocked above).
            # So re.sub is safe here given the checks.
            
            new_content = re.sub(pattern, replacement_text, content, flags=flags)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return f"Successfully edited {path}. Replaced {count} occurrence(s)."

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
                        "description": "The exact block of text (or regex pattern) to replace."
                    },
                    "replacement_text": {
                        "type": "string",
                        "description": "The new text to insert in place of target_text."
                    },
                    "regex": {
                        "type": "boolean",
                        "description": "Treat target_text as a regex pattern. Default False."
                    },
                    "case_insensitive": {
                        "type": "boolean",
                        "description": "Perform case-insensitive matching. Default False."
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace all occurrences if multiple found. Default False."
                    }
                },
                "required": ["path", "target_text", "replacement_text"]
            }
        }
