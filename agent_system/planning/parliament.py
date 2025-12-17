from typing import List, Tuple
from .deputy import Deputy
from .president import President

class Parliament:
    def __init__(self, president: President, deputies: List[Deputy], ui=None):
        self.president = president
        self.deputies = deputies
        self.ui = ui

    def _log(self, message, style=None):
        if self.ui:
            self.ui.console.print(message, style=style)
        else:
            print(message)

    def conduct_session(self, objective: str, tools_description: str) -> str:
        self._log(f"\n[bold magenta]--- Parliament Session Started ---[/bold magenta]")
        self._log(f"Objective: {objective}")
        
        # 1. President creates initial plan
        self._log("[bold yellow]President is creating the initial plan...[/bold yellow]")
        current_plan = self.president.create_plan(objective, tools_description)
        self._log(f"\n[bold cyan][Initial Plan]:[/bold cyan]\n{current_plan}\n")

        max_rounds = 3
        for round_num in range(1, max_rounds + 1):
            if self.ui:
                self.ui.print_parliament_header(round_num)
            else:
                self._log(f"[bold magenta]--- Round {round_num} of Voting ---[/bold magenta]")
            
            votes = []
            feedback_list = []
            
            # 2. Deputies vote
            valid_votes = 0
            yes_votes = 0
            
            for deputy in self.deputies:
                review = deputy.review_plan(current_plan, objective, tools_description)
                
                if "error" in review:
                    self._log(f"  -> Deputy [bold]{deputy.name}[/bold]: [bold red]ERROR[/bold red] | {review['error']}")
                    continue
                
                vote = review.get("vote", False)
                note = review.get("note", "No comment")
                
                valid_votes += 1
                if vote:
                    yes_votes += 1
                    
                feedback_list.append({"deputy": deputy.name, "note": note, "vote": vote})
                
                if self.ui:
                    self.ui.print_deputy_vote(deputy.name, vote, note)
                else:
                    status = "[bold green]YES[/bold green]" if vote else "[bold red]NO[/bold red]"
                    self._log(f"  -> Deputy [bold]{deputy.name}[/bold]: {status} | Note: [dim]{note}[/dim]")

            # 3. Check Consensus
            if valid_votes == 0:
                self._log("[bold yellow]No valid votes received (all deputies failed). Proceeding with current plan.[/bold yellow]")
                return current_plan

            self._log(f"Result: {yes_votes}/{valid_votes} YES votes.")

            if yes_votes == valid_votes:
                self._log("[bold green]>>> Consensus Reached! Plan Approved. <<<[/bold green]")
                return current_plan
            
            # 4. Revise Plan if not approved
            if round_num < max_rounds:
                self._log("[bold yellow]Consensus not reached. President is revising the plan...[/bold yellow]")
                current_plan = self.president.revise_plan(current_plan, feedback_list, objective)
                self._log(f"\n[bold cyan][Revised Plan V{round_num + 1}]:[/bold cyan]\n{current_plan}\n")
            else:
                self._log("[bold red]Max rounds reached. Proceeding with current plan despite lack of full consensus.[/bold red]")
                return current_plan

        return current_plan
