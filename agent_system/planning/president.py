from typing import List, Dict, Any
import json
import re

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

    def should_plan(self, objective: str, tools_description: str) -> Dict[str, Any]:
        """
        Decide whether the request needs a full parliament plan.
        Returns {"plan": bool, "reason": str}.
        """
        system_prompt = (
            "You are the President of the AI Parliament.\n"
            "Task: Decide if the user's objective needs a full planning session.\n"
            "Return JSON only: {\"plan\": true/false, \"reason\": \"brief justification\"}.\n"
            "Use plan=false for greetings, short factual answers, or single-step/tool tasks.\n"
            "Use plan=true for multi-step, ambiguous, or risky tasks that benefit from review."
        )

        user_message = (
            f"Objective: {objective}\n\n"
            f"Available Tools:\n{tools_description}\n\n"
            "Decide if planning is necessary."
        )

        content = self.provider.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=self.model,
            max_tokens=400
        )

        # Robust JSON extraction
        match = re.search(r"\{.*\}", content, re.DOTALL)
        json_str = match.group(0) if match else content
        try:
            data = json.loads(json_str)
            plan = bool(data.get("plan", True))
            reason = data.get("reason", "No reason provided.")
            return {"plan": plan, "reason": reason}
        except Exception:
            # Default to planning if parsing fails
            return {"plan": True, "reason": "Fallback to plan (unable to parse decision)."}
