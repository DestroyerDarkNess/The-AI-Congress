from typing import List, Dict

class President:
    def __init__(self, model: str, provider):
        self.model = model
        self.provider = provider

    def create_plan(self, objective: str, tools_description: str) -> str:
        system_prompt = (
            "You are the President of the AI Parliament.\n"
            "Your Goal: Create a detailed, step-by-step plan to achieve the User's Objective.\n"
            "You have access to specific Tools. The plan should be clear and actionable.\n"
            "Format: Markdown list."
        )

        user_message = (
            f"Objective: {objective}\n\n"
            f"Available Tools:\n{tools_description}\n\n"
            "Please create the initial plan."
        )

        return self.provider.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=self.model,
            max_tokens=2000
        )

    def revise_plan(self, current_plan: str, feedback_list: List[Dict], objective: str) -> str:
        feedback_str = "\n".join([f"- {f['deputy']}: {f['note']}" for f in feedback_list])
        
        system_prompt = (
            "You are the President of the AI Parliament.\n"
            "Your Goal: Revise the current plan based on the feedback from the Deputies.\n"
            "Incorporate valid suggestions and improve the plan.\n"
            "Format: Markdown list."
        )

        user_message = (
            f"Objective: {objective}\n\n"
            f"Current Plan:\n{current_plan}\n\n"
            f"Feedback from Parliament:\n{feedback_str}\n\n"
            "Please provide the Revised Plan (V2)."
        )

        return self.provider.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=self.model,
            max_tokens=2000
        )
