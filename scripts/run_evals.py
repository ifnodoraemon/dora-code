#!/usr/bin/env python3
"""Minimal real-agent eval runner."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evals.agent_adapter import create_doraemon_agent
from tests.evals.agent_evaluator import AgentEvaluator


def load_tasks(category: str | None = None) -> list[dict]:
    tasks: list[dict] = []
    tasks_dir = Path("tasks")
    pattern = f"{category}/*.json" if category else "**/*.json"

    for task_file in sorted(tasks_dir.glob(pattern)):
        with open(task_file, encoding="utf-8") as f:
            data = json.load(f)
        tasks.extend(data if isinstance(data, list) else [data])

    return tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real agent evaluations")
    parser.add_argument("--category", choices=["basic", "advanced", "adversarial"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    if not args.all and not args.category:
        parser.error("Specify --category or --all")

    tasks = load_tasks(None if args.all else args.category)
    if args.limit > 0:
        tasks = tasks[: args.limit]

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(tasks, tmp, ensure_ascii=False, indent=2)
        temp_task_file = tmp.name

    evaluator = AgentEvaluator(temp_task_file)
    agent = create_doraemon_agent()
    try:
        report = evaluator.run_evaluation(agent)
        evaluator.print_report(report)
        return 0 if report["summary"]["success_rate"] > 0 else 1
    finally:
        agent.close()


if __name__ == "__main__":
    raise SystemExit(main())
