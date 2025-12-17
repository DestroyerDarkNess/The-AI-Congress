import os
from dotenv import load_dotenv

from agent_system.core import Agent
from agent_system.tools import ALL_TOOLS
from agent_system.planning import President, Deputy, Parliament
from agent_system.llm import OpenAILikeProvider
from agent_system.ui import ui

# Load environment variables
load_dotenv()

# Initialize LLM Provider
provider = OpenAILikeProvider(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://unifiedai.runasp.net/v1"
)

def main():
    ui.print_welcome(model="moonshot-MBZUAI-IFM/K2-Think")
    
    # Initialize tools
    tools = ALL_TOOLS
    tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in tools])
    
    # Initialize Parliament
    president = President(model="moonshot-MBZUAI-IFM/K2-Think", provider=provider)
    deputies = [
        Deputy(
            name="Architect",
            model="moonshot-MBZUAI-IFM/K2-Think",
            persona="You are a Software Architect. You focus on modularity, clean code, and scalability. You are critical of messy or unstructured plans.",
            provider=provider
        ),
        Deputy(
            name="Security",
            model="moonshot-MBZUAI-IFM/K2-Think",
            persona="You are a Security Expert. You focus on safety, permissions, and avoiding dangerous commands. You are critical of loose file permissions or shell usage.",
            provider=provider
        ),
        Deputy(
            name="Product Manager",
            model="moonshot-MBZUAI-IFM/K2-Think",
            persona="You are a Product Manager. You focus on user value and simplicity. You ensure the plan actually solves the user's request efficiently.",
            provider=provider
        )
    ]
    parliament = Parliament(president=president, deputies=deputies, ui=ui)
    
    # Initialize Agent
    system_prompt = "You are a helpful AI assistant capable of using tools to interact with the file system."

    agent = Agent(provider=provider, tools=tools, system_prompt=system_prompt, model="moonshot-MBZUAI-IFM/K2-Think", ui=ui)
    
    ui.console.print("[bold green]Agent ready.[/bold green] Type [bold red]'exit'[/bold red] to quit.")
    
    while True:
        try:
            user_input = ui.input()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                ui.console.print("[bold red]Goodbye![/bold red]")
                break

            ui.print_user_message(user_input)

            decision = president.should_plan(user_input, tools_desc)
            should_plan = decision.get("plan", True)
            reason = decision.get("reason", "No reason provided.")

            if not should_plan:
                ui.console.print(f"[bold yellow]Skipping planning[/bold yellow]: {reason}")
                direct_prompt = (
                    f"Objective: {user_input}\n\n"
                    f"The president decided planning is not required because: {reason}\n"
                    "Respond directly. Use tools only if they clearly add value."
                )
                response = agent.run(direct_prompt)
                ui.print_assistant_message(response)
                continue
            
            # 1. Parliament Session
            with ui.status("Parliament is in session..."):
                approved_plan = parliament.conduct_session(user_input, tools_desc)
            
            # 2. Agent Execution
            ui.console.print("[bold green]Agent is executing the plan...[/bold green]")
            execution_prompt = (
                f"Objective: {user_input}\n\n"
                f"APPROVED PLAN:\n{approved_plan}\n\n"
                "Please execute this plan step by step. Use the tools as needed."
            )
            
            response = agent.run(execution_prompt)
            
            ui.print_assistant_message(response)
            
        except KeyboardInterrupt:
            ui.console.print("\n[bold red]Goodbye![/bold red]")
            break
        except Exception as e:
            ui.console.print(f"\n[bold red]An error occurred:[/bold red] {e}")


if __name__ == "__main__":
    main()
