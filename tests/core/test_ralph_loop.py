from src.core.ralph_loop import RalphLoopManager


def test_ralph_manager_add_choose_and_complete_task(tmp_path):
    mgr = RalphLoopManager(project_dir=tmp_path)
    mgr.init_storage()
    task = mgr.add_task("Optimize startup latency", "Startup should be faster.")

    assert task.title == "Optimize startup latency"

    next_task = mgr.choose_next_task()
    assert next_task is not None
    assert next_task.id == task.id
    assert next_task.status == "in_progress"
    assert "[Ralph Task" in next_task.last_prompt
    assert mgr.get_active_task() is not None
    assert mgr.get_active_task().id == task.id

    assert mgr.mark_done(task.id, "validated") is True
    assert mgr.get_task(task.id).status == "completed"
    assert mgr.get_active_task() is None


def test_ralph_manager_marks_task_blocked(tmp_path):
    mgr = RalphLoopManager(project_dir=tmp_path)
    task = mgr.add_task("Investigate flaky test")

    assert mgr.mark_blocked(task.id, "need repro steps") is True
    blocked = mgr.get_task(task.id)
    assert blocked is not None
    assert blocked.status == "blocked"
    assert blocked.notes[-1] == "blocked: need repro steps"


def test_ralph_manager_suggests_outcome_from_run_state(tmp_path):
    mgr = RalphLoopManager(project_dir=tmp_path)
    task = mgr.add_task("Improve test stability")
    mgr.choose_next_task()

    kind, command = mgr.suggest_outcome(
        task.id,
        files_modified=["src/app.py"],
        verification_performed=True,
        is_stuck=False,
        recent_failures=[],
    )
    assert kind == "done"
    assert command.startswith(f"/ralph done {task.id}")

    kind, command = mgr.suggest_outcome(
        task.id,
        files_modified=[],
        verification_performed=False,
        is_stuck=True,
        recent_failures=["tests keep timing out"],
    )
    assert kind == "blocked"
    assert command.startswith(f"/ralph blocked {task.id}")
