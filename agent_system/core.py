from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
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

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        
        while True:
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
                
                # Add a system reminder to the tool output to keep the agent on track
                self.messages.append({
                    "role": "user", 
                    "content": f"Tool Output: {result}\n\n(Remember to use this information to answer the user's original request: '{user_input}')"
                })

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
