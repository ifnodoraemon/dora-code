#!/usr/bin/env python3
"""Run professional coding benchmarks against the real agent."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evals.professional_benchmarks import ProfessionalBenchmarkRunner
from tests.evals.agent_adapter import create_doraemon_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run professional coding benchmarks")
    parser.add_argument(
        "--suite",
        choices=["humaneval_plus", "repo_patch", "terminal_bench", "real_repo"],
        required=True,
    )
    parser.add_argument("--dataset", help="Optional dataset JSON path")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    agent = create_doraemon_agent()
    try:
        runner = ProfessionalBenchmarkRunner(agent)
        report = runner.run(args.suite, dataset_path=args.dataset, limit=args.limit)
    finally:
        agent.close()

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if report["pass_rate"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
