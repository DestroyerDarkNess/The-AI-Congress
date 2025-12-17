import os
import time
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from rich.style import Style
from rich.theme import Theme
from rich.live import Live
from rich.spinner import Spinner
from rich.layout import Layout
from rich.prompt import Prompt
from rich.box import ROUNDED

# --- Colors from Letta Code ---
COLORS = {
    "orange": "#FF5533",
    "blue": "#0707AC",
    "primaryAccent": "#8C8CF9",
    "primaryAccentLight": "#BEBEEE",
    "textMain": "#DEE1E4",
    "textSecondary": "#A5A8AB",
    "textDisabled": "#46484A",
    "statusSuccess": "#64CF64",
    "statusWarning": "#FEE19C",
    "statusError": "#F1689F",
    "toolStreaming": "#46484A",
    "toolPending": "#A5A8AB",
    "toolRunning": "#FEE19C",
    "toolCompleted": "#64CF64",
    "toolError": "#F1689F",
    "inputPrompt": "#DEE1E4",
    "welcomeAccent": "#8C8CF9",
}

# --- ASCII Art ---
ASCII_LOGO = r"""
                @@@             
                @@@@@           
             @@@@@@             
          @@@@@  @@@@@          
        @@@          @@@        
       @@@            @@@       
       @@@@@@@@@@@@@@@@@@       
       @@ @@ @ @@ @ @@ @@       
       @@ @@ @ @@ @ @@ @@       
@@@===@@@@@@@@@@@@@@@@@@@@===@@@
@@                            @@
@@ @@@ @@@@ @@@ @@@  @@@ @@@  @@
@@ @@@  @@  @@@  @@  @@@ @@@  @@
@@ @@@ @@@@ @@@ @@@  @@@ @@@  @@
@@ @@@ @@@@ @@@ @@@  @@@ @@@  @@
@@                            @@
@@@==========================@@@
"""

class UI:
    def __init__(self):
        self.theme = Theme({
            "primary": COLORS["primaryAccent"],
            "secondary": COLORS["textSecondary"],
            "success": COLORS["statusSuccess"],
            "warning": COLORS["statusWarning"],
            "error": COLORS["statusError"],
            "dim": COLORS["textDisabled"],
            "markdown.h1": f"bold {COLORS['primaryAccent']}",
            "markdown.h2": f"bold {COLORS['primaryAccentLight']}",
            "markdown.item": "white",
            "markdown.code": "cyan",
        })
        self.console = Console(theme=self.theme)
        self.spinner = Spinner("dots", style=COLORS["primaryAccent"])

    def _create_gutter_table(self, gutter_content, main_content):
        """Creates a 2-column table for the gutter layout."""
        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold", width=2, justify="center")
        table.add_column(ratio=1)
        table.add_row(gutter_content, main_content)
        return table

    def print_welcome(self, version="2.1", model="unknown"):
        """Prints the welcome screen."""
        self.console.print()
        
        # Logo lines
        logo_lines = ASCII_LOGO.strip().split("\n")
        
        # Create a grid for the welcome screen
        grid = Table.grid(padding=(0, 2))
        grid.add_column()
        grid.add_column()
        
        # Left column: Logo
        logo_text = Text()
        for line in logo_lines:
            logo_text.append(f"  {line}\n", style=COLORS["welcomeAccent"])
        
        # Right column: Info
        info_text = Text()
        info_text.append("The AI Congress\n", style="bold white")
        info_text.append(f" v{version}\n", style="dim white")
        info_text.append(f"{model} · API Key Auth\n", style="dim white")
        info_text.append(f"{os.getcwd()}\n", style="dim white")
        
        grid.add_row(logo_text, info_text)
        self.console.print(grid)
        self.console.print()

    def print_user_message(self, text: str):
        """Prints a user message with the '> ' gutter."""
        gutter = Text(">", style=COLORS["inputPrompt"])
        content = Markdown(text)
        self.console.print(self._create_gutter_table(gutter, content))
        self.console.print()

    def print_assistant_message(self, text: str):
        """Prints an assistant message with the '● ' gutter."""
        gutter = Text("●", style="white")
        content = Markdown(text)
        self.console.print(self._create_gutter_table(gutter, content))
        self.console.print()

    def print_tool_call(self, name: str, args: str):
        """Prints a tool call with the '● ' gutter."""
        gutter = Text("●", style=COLORS["toolRunning"]) # Initially running/pending
        
        # Format args nicely
        content = Text()
        content.append(name, style="bold white")
        content.append(" ")
        content.append(f"({args})", style="dim white")
        
        self.console.print(self._create_gutter_table(gutter, content))

    def print_tool_result(self, result: str, is_error: bool = False):
        """Prints a tool result with the '  ⎿  ' indentation."""
        prefix = Text("  ⎿  ", style="dim white")
        
        style = COLORS["toolError"] if is_error else "white"
        
        # Truncate if too long for display (logic from original code)
        display_text = result
        if len(display_text) > 500:
             display_text = display_text[:500] + "..."

        content = Text(display_text, style=style)
        
        # Use a grid to align the prefix and content
        grid = Table.grid(padding=(0, 0))
        grid.add_column(width=5)
        grid.add_column(ratio=1)
        grid.add_row(prefix, content)
        
        self.console.print(grid)
        self.console.print()

    def print_plan(self, title: str, plan_text: str):
        """Prints the plan rendered as Markdown in a Panel."""
        md = Markdown(plan_text)
        panel = Panel(
            md, 
            title=title, 
            border_style=COLORS['primaryAccentLight'], 
            box=ROUNDED, 
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def print_parliament_header(self, round_num: int):
        self.console.print(f"[{COLORS['primaryAccent']}]--- Round {round_num} of Voting ---[/{COLORS['primaryAccent']}]")

    def print_deputy_vote(self, name: str, vote: bool, note: str):
        status = f"[{COLORS['statusSuccess']}]YES[/{COLORS['statusSuccess']}]" if vote else f"[{COLORS['statusError']}]NO[/{COLORS['statusError']}]"
        self.console.print(f"  -> Deputy [bold]{name}[/bold]: {status} | Note: [dim]{note}[/dim]")

    def print_stream_chunk(self, chunk: str):
        """Prints a chunk of text directly (for streaming)."""
        self.console.print(chunk, end="")

    def input(self, prompt_text: str = "") -> str:
        """Custom input with styled prompt."""
        # Print the divider line
        width = self.console.width
        self.console.print(f"[{COLORS['textDisabled']}]" + "─" * width + f"[/{COLORS['textDisabled']}]")
        
        # Print the prompt row
        prompt_style = Style(color=COLORS["inputPrompt"])
        return Prompt.ask(f"[{COLORS['inputPrompt']}]> [/{COLORS['inputPrompt']}]", console=self.console)

    def status(self, message: str):
        """Returns a status context manager."""
        return self.console.status(message, spinner="dots", spinner_style=COLORS["primaryAccent"])

# Global UI instance
ui = UI()
