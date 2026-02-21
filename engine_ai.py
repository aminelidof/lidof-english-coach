from groq import Groq
import json
import re

class EliasBrain:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def process_interaction(self, user_input, history, scenario="General", level="Intermediate"):
        system_prompt = f"""
        ROLE: Elite English Coach (Elias). Level: {level}. Scenario: {scenario}.
        You are a warm, professional mentor. Speak naturally but keep it simple for {level} learners.
        STRICT JSON FORMAT:
        {{
          "reply": "Your natural spoken response",
          "analysis": {{
            "corrected": "Native version of user's input",
            "rule": "Very short grammar tip in French (15 words max)",
            "score": 0-100
          }}
        }}
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-8:])
        messages.append({"role": "user", "content": user_input})

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            content = completion.choices[0].message.content
            # Extraction Regex pour garantir la stabilité SaaS
            match = re.search(r'\{.*\}', content, re.DOTALL)
            return json.loads(match.group())
        except:
            return {
                "reply": "I'm ready when you are! Could you repeat that?", 
                "analysis": {"corrected": "N/A", "rule": "Connection error", "score": 100}
            }