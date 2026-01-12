import asyncio
import json
import os
import sys
from typing import List, Dict
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from src.evals.model_grader import ModelGrader
from src.host.cli import run_task_for_eval

console = Console()

class EvaluationHarness:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.grader = ModelGrader()
        self.results = []

    def load_tasks(self) -> List[Dict]:
        with open(self.dataset_path, "r") as f:
            if self.dataset_path.endswith(".jsonl"):
                return [json.loads(line) for line in f]
            else:
                return json.load(f)

    async def run(self):
        tasks = self.load_tasks()
        console.print(f"[bold]Starting Evaluation on {len(tasks)} tasks...[/bold]")
        
        for i, task in enumerate(tasks):
            console.print(f"\n--- Task {i+1}: {task['id']} ---")
            console.print(f"[dim]Prompt: {task['prompt']}[/dim]")
            
            # 1. Run Agent
            # 注意：Eval 期间可能会产生真实副作用（写文件），建议在容器或沙箱中运行
            # 这里我们简单运行，因为这是本地开发环境
            agent_output = await run_task_for_eval(task['prompt'], project="eval_run")
            console.print(f"[cyan]Agent Output:[/cyan]\n{agent_output[:200]}...")
            
            # 2. Grade
            rubric = task.get("rubric", "The answer must be correct, helpful, and safe.")
            grade_result = self.grader.grade(
                task=task['prompt'],
                agent_output=agent_output,
                rubric=rubric
            )
            
            # 3. Record
            result_record = {
                "task_id": task['id'],
                "prompt": task['prompt'],
                "output": agent_output,
                "score": grade_result['score'],
                "pass": grade_result['pass'],
                "reasoning": grade_result['reasoning']
            }
            self.results.append(result_record)
            
            color = "green" if grade_result['pass'] else "red"
            console.print(f"[{color}]Score: {grade_result['score']}/5 - {grade_result['reasoning']}[/{color}]")

        self.print_summary()

    def print_summary(self):
        table = Table(title="Evaluation Summary")
        table.add_column("ID", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Pass", style="green")
        table.add_column("Reasoning")
        
        total_score = 0
        passed_count = 0
        
        for res in self.results:
            table.add_row(
                res['task_id'], 
                str(res['score']),
                "✅" if res['pass'] else "❌",
                res['reasoning'][:100] + "..."
            )
            total_score += res['score']
            if res['pass']: passed_count += 1
            
        console.print(table)
        console.print(f"\n[bold]Final Pass Rate: {passed_count}/{len(self.results)} ({passed_count/len(self.results)*100:.1f}%)[/bold]")
        console.print(f"[bold]Average Score: {total_score/len(self.results):.2f}[/bold]")

if __name__ == "__main__":
    # Create a dummy dataset if not exists
    dummy_data_path = "polymath/tests/evals/dataset.json"
    if not os.path.exists(dummy_data_path):
        dummy_data = [
            {
                "id": "write-001",
                "prompt": "Write a short poem about the Rust programming language.",
                "rubric": "Must mention memory safety and borrow checker. Must be poetic."
            },
            {
                "id": "code-001",
                "prompt": "Write a python script to print the first 5 prime numbers.",
                "rubric": "Code must be syntactically correct and logic must produce 2, 3, 5, 7, 11."
            }
        ]
        with open(dummy_data_path, "w") as f:
            json.dump(dummy_data, f, indent=2)
            
    harness = EvaluationHarness(dummy_data_path)
    asyncio.run(harness.run())
