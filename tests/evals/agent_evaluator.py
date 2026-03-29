"""
Minimal real-agent evaluator.

Runs tasks in isolated sandboxes and evaluates against the production trace/tool names.
"""

import json
import os
import re
import tempfile
import time
from pathlib import Path


class AgentEvaluator:
    """Evaluate real agent runs against task assertions."""

    def __init__(self, task_file: str):
        self.tasks = self.load_tasks(task_file)
        self.results: list[dict] = []

    def load_tasks(self, task_file: str) -> list[dict]:
        with open(task_file, encoding="utf-8") as f:
            return json.load(f)

    def evaluate_task(self, agent, task: dict) -> dict:
        result = {
            "task_id": task.get("id", "unknown"),
            "task_name": task.get("name", task.get("id", "unknown")),
            "difficulty": task.get("difficulty", "medium"),
            "category": task.get("category", "general"),
            "success": False,
            "execution_time": 0.0,
            "tool_calls": [],
            "errors": [],
            "assertions": {"success": False, "reasons": []},
        }

        original_cwd = Path.cwd()

        with tempfile.TemporaryDirectory(prefix=f"eval_{result['task_id']}_") as sandbox:
            sandbox_dir = Path(sandbox)
            try:
                self._materialize_setup(task.get("setup", {}), sandbox_dir)
                os.chdir(sandbox_dir)

                start_time = time.time()
                response = agent.execute(task["prompt"])
                result["execution_time"] = time.time() - start_time
                result["tool_calls"] = self.extract_tool_calls(response)

                assertions = task.get("assertions", [])
                if assertions:
                    result["assertions"] = self.check_assertions(response, assertions, sandbox_dir)
                    result["success"] = result["assertions"]["success"]
                else:
                    result["success"] = response.success

                result["trace_path"] = response.metadata.get("trace_path")

            except Exception as e:
                result["errors"].append(str(e))
            finally:
                os.chdir(original_cwd)

        return result

    def _materialize_setup(self, setup: dict, sandbox_dir: Path) -> None:
        for relative_path, content in setup.get("files", {}).items():
            file_path = sandbox_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

    def extract_tool_calls(self, response) -> list[str]:
        if hasattr(response, "tool_calls"):
            return [tc.name for tc in response.tool_calls]
        return []

    def check_assertions(self, response, assertions: list[dict], sandbox_dir: Path) -> dict:
        reasons: list[str] = []
        success = True
        tool_calls = self.extract_tool_calls(response)
        output = getattr(response, "output", "") or ""

        for assertion in assertions:
            atype = assertion.get("type")

            if atype == "file_exists":
                path = assertion["path"]
                matched = list(sandbox_dir.glob(path)) if "*" in path else [sandbox_dir / path]
                ok = any(p.exists() for p in matched)
                reasons.append(f"{'PASS' if ok else 'FAIL'} file_exists: {path}")
                success = success and ok
                continue

            if atype == "tool_used":
                tool = assertion["tool"]
                ok = tool in tool_calls
                reasons.append(f"{'PASS' if ok else 'FAIL'} tool_used: {tool}")
                success = success and ok
                continue

            if atype == "tool_not_used":
                tool = assertion["tool"]
                ok = tool not in tool_calls
                reasons.append(f"{'PASS' if ok else 'FAIL'} tool_not_used: {tool}")
                success = success and ok
                continue

            if atype == "output_contains":
                pattern = assertion["pattern"]
                ok = pattern.lower() in output.lower()
                reasons.append(f"{'PASS' if ok else 'FAIL'} output_contains: {pattern}")
                success = success and ok
                continue

            if atype == "pattern_exists":
                pattern = assertion["pattern"]
                ok = self._pattern_exists(pattern, sandbox_dir)
                reasons.append(f"{'PASS' if ok else 'FAIL'} pattern_exists: {pattern}")
                success = success and ok
                continue

            if atype == "pattern_not_exists":
                pattern = assertion["pattern"]
                ok = not self._pattern_exists(pattern, sandbox_dir)
                reasons.append(f"{'PASS' if ok else 'FAIL'} pattern_not_exists: {pattern}")
                success = success and ok
                continue

            if atype == "file_not_exists":
                path = assertion["path"]
                ok = not (sandbox_dir / path).exists() if not Path(path).is_absolute() else not Path(path).exists()
                reasons.append(f"{'PASS' if ok else 'FAIL'} file_not_exists: {path}")
                success = success and ok
                continue

            if atype == "syntax_valid":
                language = assertion.get("language")
                ok = self._syntax_valid(sandbox_dir, language)
                reasons.append(f"{'PASS' if ok else 'FAIL'} syntax_valid: {language}")
                success = success and ok
                continue

            if atype == "error_raised":
                error_type = assertion["error_type"]
                errors = " ".join(getattr(response, "errors", [])).lower()
                ok = error_type.lower() in errors
                reasons.append(f"{'PASS' if ok else 'FAIL'} error_raised: {error_type}")
                success = success and ok
                continue

            reasons.append(f"SKIP unsupported_assertion: {atype}")

        return {"success": success, "reasons": reasons}

    def _pattern_exists(self, pattern: str, sandbox_dir: Path) -> bool:
        for file_path in sandbox_dir.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False

    def _syntax_valid(self, sandbox_dir: Path, language: str | None) -> bool:
        if language != "python":
            return True
        for file_path in sandbox_dir.rglob("*.py"):
            try:
                compile(file_path.read_text(encoding="utf-8", errors="replace"), str(file_path), "exec")
            except SyntaxError:
                return False
        return True

    def run_evaluation(self, agent) -> dict:
        print(f"开始评估 {len(self.tasks)} 个任务...")
        self.results = []

        for task in self.tasks:
            task_name = task.get("name", task.get("id", "Unknown"))
            print(f"\n评估任务: {task_name} (难度: {task['difficulty']})")
            result = self.evaluate_task(agent, task)
            self.results.append(result)
            status = "✅ 成功" if result["success"] else "❌ 失败"
            print(f"  {status} - 耗时: {result['execution_time']:.2f}s")

        return self.generate_report()

    def generate_report(self) -> dict:
        total_tasks = len(self.results)
        successful_tasks = sum(1 for r in self.results if r["success"])
        by_category: dict[str, dict[str, int]] = {}
        by_difficulty: dict[str, dict[str, int]] = {}

        for result in self.results:
            for bucket, key in ((by_category, result["category"]), (by_difficulty, result["difficulty"])):
                stats = bucket.setdefault(key, {"total": 0, "success": 0})
                stats["total"] += 1
                if result["success"]:
                    stats["success"] += 1

        return {
            "summary": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "success_rate": successful_tasks / total_tasks if total_tasks else 0.0,
                "avg_execution_time": (
                    sum(r["execution_time"] for r in self.results) / total_tasks if total_tasks else 0.0
                ),
            },
            "by_category": by_category,
            "by_difficulty": by_difficulty,
            "failed_tasks": [r for r in self.results if not r["success"]],
        }

    def print_report(self, report: dict) -> None:
        print("\n" + "=" * 60)
        print("Agent 效果评估报告")
        print("=" * 60)

        summary = report["summary"]
        print("\n总体表现:")
        print(f"  总任务数: {summary['total_tasks']}")
        print(f"  成功任务: {summary['successful_tasks']}")
        print(f"  成功率: {summary['success_rate'] * 100:.1f}%")
        print(f"  平均耗时: {summary['avg_execution_time']:.2f}s")

        if report["failed_tasks"]:
            print("\n失败任务:")
            for task in report["failed_tasks"]:
                print(f"  - {task['task_name']} (ID: {task['task_id']})")
                for reason in task.get("assertions", {}).get("reasons", [])[:4]:
                    if reason.startswith("FAIL"):
                        print(f"    {reason}")
