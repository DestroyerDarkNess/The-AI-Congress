import fnmatch
import os
import re
from typing import Any, Dict, Iterable, List

from ..core import Tool


class SearchTextTool(Tool):
    @property
    def name(self) -> str:
        return "search_text"

    @property
    def description(self) -> str:
        return "Search for a text/regex pattern in files (grep-like). Returns matching file:line results."

    def _iter_files(self, path: str, include_globs: List[str]) -> Iterable[str]:
        if os.path.isfile(path):
            yield path
            return

        ignore_dirs = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            ".pytest_cache",
            "node_modules",
            "dist",
            "build",
        }

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for filename in files:
                if include_globs and not any(fnmatch.fnmatch(filename, g) for g in include_globs):
                    continue
                yield os.path.join(root, filename)

    def _is_binary_file(self, file_path: str) -> bool:
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(4096)
            return b"\x00" in chunk
        except Exception:
            return True

    def execute(
        self,
        pattern: str,
        path: str = ".",
        include: str = "*",
        max_results: int = 50,
        case_sensitive: bool = False,
        regex: bool = True,
    ) -> str:
        try:
            if not pattern:
                return "Error: 'pattern' is required."

            max_results = int(max_results)
            if max_results <= 0:
                max_results = 50
            max_results = min(max_results, 500)

            include_globs = [g.strip() for g in str(include).split(",") if g.strip()]

            if not os.path.exists(path):
                return f"Error: Path does not exist: {path}"

            flags = 0 if bool(case_sensitive) else re.IGNORECASE
            compiled = re.compile(pattern, flags=flags) if bool(regex) else None

            results: List[str] = []
            truncated = False

            base_path = os.path.abspath(path if os.path.isdir(path) else os.path.dirname(path) or ".")

            for file_path in self._iter_files(path, include_globs):
                if self._is_binary_file(file_path):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line in enumerate(f, start=1):
                            haystack = line if bool(case_sensitive) else line.lower()
                            needle = pattern if bool(case_sensitive) else pattern.lower()
                            matched = (
                                bool(compiled.search(line)) if compiled else (needle in haystack)
                            )
                            if not matched:
                                continue

                            rel = os.path.relpath(file_path, start=base_path)
                            preview = line.rstrip("\r\n")
                            results.append(f"{rel}:{line_num}: {preview}")
                            if len(results) >= max_results:
                                truncated = True
                                break
                except Exception:
                    continue

                if truncated:
                    break

            header = (
                f"[search_text] pattern={pattern!r} path={path!r} results={len(results)} "
                f"truncated={'true' if truncated else 'false'}"
            )
            return header + ("\n" + "\n".join(results) if results else "\n(No matches found.)")
        except Exception as e:
            return f"Error searching text: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex (default) or literal pattern to search for."
                    },
                    "path": {
                        "type": "string",
                        "description": "Root directory or file path to search (default: '.')."
                    },
                    "include": {
                        "type": "string",
                        "description": "Comma-separated filename globs to include (default: '*'). Example: '*.py,*.md'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of matches to return (default: 50; max: 500)."
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Case-sensitive search (default: false)."
                    },
                    "regex": {
                        "type": "boolean",
                        "description": "Treat pattern as regex (default: true)."
                    },
                },
                "required": ["pattern"],
            },
        }
