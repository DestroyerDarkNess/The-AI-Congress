import json
from typing import Dict, Any

class Deputy:
    def __init__(self, name: str, model: str, persona: str, provider):
        self.name = name
        self.model = model
        self.persona = persona
        self.provider = provider

    def review_plan(self, plan: str, objective: str, tools_description: str) -> Dict[str, Any]:
        content = ""
        system_prompt = (
            f"You are {self.name}, a Deputy in the AI Parliament.\n"
            f"Your Persona: {self.persona}\n\n"
            "Your Goal: Review the proposed plan to achieve the Objective using the available Tools.\n"
            "You must Vote YES if the plan is solid, or NO if it has flaws.\n"
            "You must provide a brief Note/Feedback explaining your vote or suggesting improvements.\n"
            "CRITICAL: Keep your note EXTREMELY CONCISE (max 2 sentences). Do not cut off your response.\n\n"
            "Response Format: JSON\n"
            "{\n"
            '  "vote": true/false,\n'
            '  "note": "Concise feedback here"\n'
            "}"
        )

        user_message = (
            f"Objective: {objective}\n\n"
            f"Available Tools:\n{tools_description}\n\n"
            f"Proposed Plan:\n{plan}\n\n"
            "Please review and vote."
        )

        try:
            content = self.provider.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model=self.model,
                max_tokens=1000
            )
            
            # Debug: Print raw content
            # print(f"\n[DEBUG] Deputy {self.name} Raw Output:\n{content}\n[END DEBUG]\n")

            # Robust JSON extraction using regex
            import re
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            
            # Fallback if no JSON found (or try parsing the whole thing)
            return json.loads(content)
        except Exception as e:
            return {"error": f"Error during review: {str(e)} | Content: {content[:100]}..."}
