import os
from typing import Dict, Any
from ..core import Tool

class ReadFileTool(Tool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read a slice of a file (safe for large files). Use start_line/max_lines to paginate."

    def execute(
        self,
        path: str,
        start_line: int = 1,
        max_lines: int = 200,
        max_chars: int = 20000,
        with_line_numbers: bool = False,
    ) -> str:
        try:
            start_line = int(start_line)
            max_lines = int(max_lines)
            max_chars = int(max_chars)

            if start_line < 1:
                start_line = 1
            if max_lines <= 0:
                max_lines = 200
            if max_chars <= 0:
                max_chars = 20000

            max_lines = min(max_lines, 2000)
            max_chars = min(max_chars, 200000)

            file_size = os.path.getsize(path)

            lines_out = []
            char_count = 0
            truncated = False
            next_start_line = None

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, start=1):
                    if line_num < start_line:
                        continue

                    if bool(with_line_numbers):
                        formatted = f"{line_num:>6} | {line}"
                    else:
                        formatted = line

                    if len(lines_out) >= max_lines or (char_count + len(formatted) > max_chars):
                        truncated = True
                        next_start_line = line_num
                        break

                    lines_out.append(formatted)
                    char_count += len(formatted)

            if not lines_out:
                header = (
                    f"[read_file] path={path} bytes={file_size} start_line={start_line} "
                    f"end_line={start_line - 1} truncated=false"
                )
                return header + "\n(No content returned.)"

            end_line = start_line + len(lines_out) - 1
            header = (
                f"[read_file] path={path} bytes={file_size} start_line={start_line} end_line={end_line} "
                f"truncated={'true' if truncated else 'false'}"
            )
            if truncated and next_start_line is not None:
                header += f" next_start_line={next_start_line}"

            return header + "\n" + "".join(lines_out)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to read."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "1-based line number to start reading from (default: 1)."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum lines to return (default: 200; max: 2000)."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default: 20000; max: 200000)."
                    },
                    "with_line_numbers": {
                        "type": "boolean",
                        "description": "Prefix returned lines with line numbers (default: false)."
                    }
                },
                "required": ["path"]
            }
        }
