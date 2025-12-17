import os
import re
from typing import Any, Dict, List, Optional, Tuple

from ..core import Tool


class ApplyPatchTool(Tool):
    @property
    def name(self) -> str:
        return "apply_patch"

    @property
    def description(self) -> str:
        return "Apply a unified-diff style patch to a file (diff engine)."

    def _strip_code_fences(self, text: str) -> str:
        lines = text.strip().splitlines()
        if not lines:
            return ""
        if lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].rstrip().endswith("```"):
            lines = lines[:-1]
        lines = [ln for ln in lines if not ln.lstrip().startswith("```")]
        return "\n".join(lines).strip("\n")

    def _detect_newline(self, raw: str) -> str:
        return "\r\n" if "\r\n" in raw else "\n"

    def _parse_hunks(self, patch_text: str) -> List[Dict[str, Any]]:
        hunks: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        hunk_re = re.compile(r"^@@\s*-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s*@@")

        for line in patch_text.splitlines():
            if line.startswith(("---", "+++")):
                continue
            if line.startswith("\\ No newline at end of file"):
                continue

            m = hunk_re.match(line)
            if m:
                old_start = int(m.group(1))
                old_count = int(m.group(2) or "1")
                new_start = int(m.group(3))
                new_count = int(m.group(4) or "1")
                current = {
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": [],
                }
                hunks.append(current)
                continue

            if current is None:
                continue

            if not line:
                # An empty diff line is a context line with empty content (rare but valid).
                current["lines"].append((" ", ""))
                continue

            prefix = line[0]
            if prefix in {" ", "+", "-"}:
                current["lines"].append((prefix, line[1:]))
            # Ignore anything else (e.g., "diff --git" lines)

        return hunks

    def _normalize(self, s: str) -> str:
        return s.rstrip("\r\n")

    def execute(self, path: str, patch: str, dry_run: bool = False) -> str:
        try:
            patch_text = self._strip_code_fences(str(patch or ""))
            if not patch_text:
                return "Error: 'patch' is required."

            if os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
                    raw = f.read()
                newline = self._detect_newline(raw)
                lines = raw.splitlines(keepends=True)
            else:
                newline = "\n"
                lines = []

            hunks = self._parse_hunks(patch_text)
            if not hunks:
                return "Error: No hunks found in patch."

            offset = 0
            for hunk in hunks:
                old_start = int(hunk["old_start"])
                idx = max(0, (old_start - 1) + offset)

                out_chunk: List[str] = []
                i = idx

                for op, text in hunk["lines"]:
                    if op in {" ", "-"}:
                        if i >= len(lines):
                            return (
                                "Error applying patch: file is shorter than expected at "
                                f"line {i + 1}."
                            )

                        current_line = lines[i]
                        if self._normalize(current_line) != self._normalize(text):
                            return (
                                "Error applying patch: context mismatch at "
                                f"line {i + 1}.\n"
                                f"Expected: {text!r}\n"
                                f"Found: {current_line.rstrip('\r\n')!r}"
                            )

                        if op == " ":
                            out_chunk.append(current_line)
                        i += 1
                        continue

                    if op == "+":
                        out_chunk.append(text + newline)
                        continue

                # Replace the affected range.
                lines[idx:i] = out_chunk
                offset += len(out_chunk) - (i - idx)

            if bool(dry_run):
                return f"Patch can be applied cleanly to {path} (dry_run=true)."

            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write("".join(lines))

            return f"Successfully applied patch to {path}."
        except Exception as e:
            return f"Error applying patch: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to patch."
                    },
                    "patch": {
                        "type": "string",
                        "description": "Unified diff patch text (hunks with @@ headers)."
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Validate patch without writing (default: false)."
                    },
                },
                "required": ["path", "patch"],
            },
        }
