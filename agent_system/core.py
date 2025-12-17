from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import json
import re

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass

    @abstractmethod
    def to_schema(self) -> Dict[str, Any]:
        pass

class Agent:
    def __init__(self, provider, tools: List[Tool], system_prompt: str = "", model: str = "zai-glm-4-flash", console=None):
        self.provider = provider
        self.tools = {t.name: t for t in tools}
        self.system_prompt = system_prompt
        self.model = model
        self.messages = []
        self.console = console
        self._max_tool_output_chars = int(os.getenv("AI_CONGRESS_MAX_TOOL_OUTPUT_CHARS", "8000"))
        self._max_tool_output_messages = int(os.getenv("AI_CONGRESS_MAX_TOOL_OUTPUT_MESSAGES", "6"))
        self._max_context_chars = int(os.getenv("AI_CONGRESS_MAX_CONTEXT_CHARS", "60000"))
        self._min_messages_to_keep = 10
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self._build_system_prompt()})

    def _log(self, message, style=None):
        if self.console:
            self.console.print(message, style=style)
        else:
            print(message)

    def _build_system_prompt(self) -> str:
        tool_descriptions = "\n".join([json.dumps(t.to_schema(), indent=2) for t in self.tools.values()])
        base_prompt = (
            f"{self.system_prompt}\n\n"
            "You have access to the following tools:\n"
            f"{tool_descriptions}\n\n"
            "To use a tool, you MUST respond with a JSON block inside markdown code fences, like this:\n"
            "```json\n"
            "{\n"
            '  "tool": "tool_name",\n'
            '  "args": { "arg_name": "value" }\n'
            "}\n"
            "```\n"
            "IMPORTANT:\n"
            "1. After receiving a Tool Output, you must use that information to FULFILL the user's original request.\n"
            "2. Do not just describe the tool output unless asked.\n"
            "3. If the user asked you to do something (e.g., create a file), and the tool output says it was successful, YOUR JOB IS DONE. Report the success to the user.\n"
            "4. If you need to find files or code but don't know where they are, ALWAYS start by using 'list_directory' with path='.' to see what is available.\n"
            "5. Use 'system_shell' ONLY for tasks not covered by other tools, or if explicitly requested. It is a powerful fallback.\n"
            "6. ACTION BIAS: If the user asks you to do something (e.g., 'create a landing page') and you have the info, DO NOT ask for permission to create the file. JUST CREATE IT using 'modify_file'.\n"
            "7. ACTION BIAS: If the user says 'go ahead', 'yes', or 'do it', EXECUTE the planned action immediately.\n"
            "8. For large files: use 'search_text' to locate relevant areas, then 'read_file' with start_line/max_lines (optionally with_line_numbers). Do NOT try to read entire huge files at once.\n"
            "9. For edits: prefer 'apply_patch' (unified diff) for targeted changes. Use 'modify_file' only when you intend to overwrite the whole file."
        )
        return base_prompt

    def _approx_context_chars(self) -> int:
        return sum(len(str(m.get("content", ""))) for m in self.messages)

    def _is_tool_output_message(self, message: Dict[str, Any]) -> bool:
        return (
            message.get("role") == "user"
            and isinstance(message.get("content"), str)
            and message["content"].startswith("Tool Output:")
        )

    def _truncate_text(self, text: str, max_chars: int) -> str:
        if not isinstance(text, str):
            text = str(text)
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text

        head = min(6000, max_chars)
        tail = min(1500, max_chars - head)
        omitted = len(text) - head - tail
        suffix = text[-tail:] if tail > 0 else ""
        return (
            f"[Tool output truncated: {len(text)} chars total; omitted {omitted} chars]\n"
            f"{text[:head]}\n...\n{suffix}"
        )

    def _enforce_context_limits(self) -> None:
        if len(self.messages) <= 2:
            return

        # 1) Ensure tool outputs are not massive.
        for message in self.messages:
            if self._is_tool_output_message(message):
                content = message.get("content", "")
                if isinstance(content, str) and len(content) > self._max_tool_output_chars:
                    prefix = "Tool Output:"
                    rest = content[len(prefix):].lstrip("\n")
                    budget = max(0, self._max_tool_output_chars - len(prefix) - 1)
                    message["content"] = f"{prefix}\n{self._truncate_text(rest, budget)}"

        # 2) Keep only the most recent N tool outputs.
        tool_indices = [i for i, m in enumerate(self.messages) if self._is_tool_output_message(m)]
        if self._max_tool_output_messages > 0 and len(tool_indices) > self._max_tool_output_messages:
            to_remove = tool_indices[: len(tool_indices) - self._max_tool_output_messages]
            for idx in reversed(to_remove):
                del self.messages[idx]

        # 3) If still too large, prune oldest tool outputs first, then oldest non-system messages.
        def system_offset() -> int:
            return 1 if self.messages and self.messages[0].get("role") == "system" else 0

        while self._approx_context_chars() > self._max_context_chars and len(self.messages) > 2:
            removed = False
            for i in range(system_offset(), len(self.messages)):
                if self._is_tool_output_message(self.messages[i]):
                    del self.messages[i]
                    removed = True
                    break

            if removed:
                continue

            if len(self.messages) <= system_offset() + self._min_messages_to_keep:
                break
            del self.messages[system_offset()]

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        
        while True:
            self._enforce_context_limits()
            # Call LLM
            if self.console:
                with self.console.status("[bold green]Thinking...", spinner="dots"):
                    response_content = self.provider.generate(self.messages, model=self.model)
            else:
                print("Thinking...")
                response_content = self.provider.generate(self.messages, model=self.model)

            self.messages.append({"role": "assistant", "content": response_content})
            
            # Check for tool calls
            tool_calls = self._parse_tool_calls(response_content)
            
            if not tool_calls:
                return response_content
            
            # Execute tools
            for tool_name, tool_args in tool_calls:
                self._log(f"[bold blue]Executing tool:[/bold blue] {tool_name} with args {tool_args}")
                
                if tool_name in self.tools:
                    try:
                        if self.console:
                            with self.console.status(f"[bold yellow]Executing {tool_name}...", spinner="bouncingBall"):
                                result = self.tools[tool_name].execute(**tool_args)
                        else:
                            result = self.tools[tool_name].execute(**tool_args)
                    except Exception as e:
                        result = f"Error executing tool: {str(e)}"
                else:
                    result = f"Error: Tool '{tool_name}' not found."
                    self._log(f"[bold red]{result}[/bold red]")

                if self.console:
                    self._log(f"[bold green]Result:[/bold green] {result[:100]}..." if len(result) > 100 else f"[bold green]Result:[/bold green] {result}")
                else:
                    print(f"Tool result: {result}")

                safe_result = self._truncate_text(result, self._max_tool_output_chars)

                # Add a system reminder to the tool output to keep the agent on track
                self.messages.append({
                    "role": "user", 
                    "content": (
                        f"Tool Output:\n{safe_result}\n\n"
                        f"(Remember to use this information to answer the user's original request: '{user_input}')"
                    )
                })

                self._enforce_context_limits()

    def _parse_tool_calls(self, content: str) -> List[tuple]:
        tool_calls = []

        # Primary channel: look for ```json code blocks
        matches = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                if "tool" in data:
                    tool_calls.append((data["tool"], data.get("args", {})))
            except json.JSONDecodeError:
                pass

        if tool_calls:
            return tool_calls

        # Fallback: scan for raw JSON objects in the stream even if fences are missing
        decoder = json.JSONDecoder()
        idx = 0
        length = len(content)

        while idx < length:
            try:
                obj, end = decoder.raw_decode(content[idx:])
                idx += end
                if isinstance(obj, dict) and "tool" in obj:
                    tool_calls.append((obj["tool"], obj.get("args", {})))
            except json.JSONDecodeError:
                idx += 1

        return tool_calls
