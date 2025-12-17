import subprocess
import platform
from typing import Dict, Any
from ..core import Tool

class SystemShellTool(Tool):
    @property
    def name(self) -> str:
        return "system_shell"

    @property
    def description(self) -> str:
        return "Execute system shell commands. Use this for advanced tasks or when other tools fail. On Windows uses PowerShell, on Linux uses /bin/sh."

    def execute(self, command: str) -> str:
        try:
            system = platform.system()
            if system == "Windows":
                shell_command = ["powershell", "-Command", command]
            else:
                shell_command = ["/bin/sh", "-c", command]
                
            result = subprocess.run(
                shell_command, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
                
            return output.strip()
        except Exception as e:
            return f"Error executing shell command: {str(e)}"

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    }
                },
                "required": ["command"]
            }
        }
