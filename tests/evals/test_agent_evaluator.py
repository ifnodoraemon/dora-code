import json

from tests.evals.agent_adapter import AgentResponse
from tests.evals.agent_evaluator import AgentEvaluator


class FailingAgent:
    def execute(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            success=False,
            output="",
            errors=["Execution failed: upstream 503"],
            metadata={"trace_path": "/tmp/fake-trace.json"},
        )


def test_evaluate_task_preserves_execution_failure(tmp_path):
    task_file = tmp_path / "tasks.json"
    task_file.write_text(
        json.dumps(
            [
                {
                    "id": "task_001",
                    "name": "task_001",
                    "difficulty": "medium",
                    "category": "general",
                    "prompt": "fix it",
                    "setup": {"files": {"app.py": "print('x')\n"}},
                    "assertions": [{"type": "tool_used", "tool": "write"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    evaluator = AgentEvaluator(str(task_file))
    result = evaluator.evaluate_task(FailingAgent(), evaluator.tasks[0])

    assert result["success"] is False
    assert result["failure_type"] == "execution_error"
    assert result["errors"] == ["Execution failed: upstream 503"]
    assert result["assertions"]["reasons"] == ["FAIL execution_error: Execution failed: upstream 503"]
    assert result["trace_path"] == "/tmp/fake-trace.json"
