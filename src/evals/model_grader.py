import os
import json
import google.generativeai as genai
from typing import Dict, Any

class ModelGrader:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set for ModelGrader")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def grade(self, task: str, agent_output: str, rubric: str) -> Dict[str, Any]:
        """
        使用 LLM 作为裁判，对 Agent 的输出进行打分。
        """
        prompt = f"""
        # Role
        You are an expert evaluator for AI agents. Your job is to grade the performance of an AI assistant based on its output.

        # Task
        {task}

        # Agent Output
        {agent_output}

        # Grading Rubric
        {rubric}

        # Instruction
        Evaluate the Agent Output against the Rubric.
        Return your response in STRICT JSON format with the following keys:
        - "score": (int) 1-5
        - "reasoning": (str) Explanation of the score
        - "pass": (bool) true if score >= 4
        """
        
        try:
            response = self.model.generate_content(prompt)
            # 尝试提取 JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception as e:
            return {"score": 0, "pass": False, "reasoning": f"Grading failed: {str(e)}"}

if __name__ == "__main__":
    # Test
    grader = ModelGrader()
    res = grader.grade(
        task="Write a haiku about code.",
        agent_output="Code flows like a stream\nBugs vanish in the clear water\nSoftware is alive",
        rubric="Must be a valid haiku (5-7-5 syllables). Must be about programming."
    )
    print(res)

