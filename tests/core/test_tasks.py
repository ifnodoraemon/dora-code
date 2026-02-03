"""Comprehensive tests for tasks.py"""
import json
import pytest
import time
from pathlib import Path
from src.core.tasks import Task, TaskStatus, TaskPriority, TaskManager


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_status_from_string(self):
        """Test creating TaskStatus from string."""
        assert TaskStatus("pending") == TaskStatus.PENDING
        assert TaskStatus("in_progress") == TaskStatus.IN_PROGRESS
        assert TaskStatus("completed") == TaskStatus.COMPLETED
        assert TaskStatus("blocked") == TaskStatus.BLOCKED
        assert TaskStatus("cancelled") == TaskStatus.CANCELLED

    def test_task_status_invalid_value(self):
        """Test TaskStatus with invalid value raises ValueError."""
        with pytest.raises(ValueError):
            TaskStatus("invalid_status")


class TestTaskPriority:
    """Tests for TaskPriority enum."""

    def test_task_priority_values(self):
        """Test TaskPriority enum values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"

    def test_task_priority_from_string(self):
        """Test creating TaskPriority from string."""
        assert TaskPriority("low") == TaskPriority.LOW
        assert TaskPriority("medium") == TaskPriority.MEDIUM
        assert TaskPriority("high") == TaskPriority.HIGH
        assert TaskPriority("critical") == TaskPriority.CRITICAL

    def test_task_priority_invalid_value(self):
        """Test TaskPriority with invalid value raises ValueError."""
        with pytest.raises(ValueError):
            TaskPriority("invalid_priority")


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation_minimal(self):
        """Test creating a task with minimal parameters."""
        task = Task(id="task_1", title="Test Task")
        assert task.id == "task_1"
        assert task.title == "Test Task"
        assert task.description == ""
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.parent_id is None
        assert task.tags == []
        assert task.subtasks == []
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_creation_full(self):
        """Test creating a task with all parameters."""
        created_at = time.time()
        updated_at = time.time()
        task = Task(
            id="task_2",
            title="Full Task",
            description="Complete description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            parent_id="parent_1",
            tags=["urgent", "bug"],
            created_at=created_at,
            updated_at=updated_at,
        )
        assert task.id == "task_2"
        assert task.title == "Full Task"
        assert task.description == "Complete description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.parent_id == "parent_1"
        assert task.tags == ["urgent", "bug"]
        assert task.created_at == created_at
        assert task.updated_at == updated_at

    def test_task_timestamps_auto_set(self):
        """Test that timestamps are automatically set if not provided."""
        before = time.time()
        task = Task(id="task_3", title="Auto Timestamp")
        after = time.time()
        assert before <= task.created_at <= after
        assert before <= task.updated_at <= after
        assert task.created_at == task.updated_at

    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = Task(
            id="task_4",
            title="Dict Task",
            description="Test description",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.LOW,
            parent_id="parent_2",
            tags=["test"],
        )
        task.subtasks = ["sub_1", "sub_2"]
        data = task.to_dict()

        assert data["id"] == "task_4"
        assert data["title"] == "Dict Task"
        assert data["description"] == "Test description"
        assert data["status"] == "completed"
        assert data["priority"] == "low"
        assert data["parent_id"] == "parent_2"
        assert data["tags"] == ["test"]
        assert data["subtasks"] == ["sub_1", "sub_2"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_task_from_dict(self):
        """Test creating task from dictionary."""
        data = {
            "id": "task_5",
            "title": "From Dict",
            "description": "Restored task",
            "status": "in_progress",
            "priority": "high",
            "parent_id": "parent_3",
            "tags": ["restored"],
            "created_at": 1234567890.0,
            "updated_at": 1234567891.0,
            "subtasks": ["sub_3"],
        }
        task = Task.from_dict(data)

        assert task.id == "task_5"
        assert task.title == "From Dict"
        assert task.description == "Restored task"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.parent_id == "parent_3"
        assert task.tags == ["restored"]
        assert task.created_at == 1234567890.0
        assert task.updated_at == 1234567891.0
        assert task.subtasks == ["sub_3"]

    def test_task_from_dict_with_defaults(self):
        """Test from_dict with missing optional fields."""
        data = {"id": "task_6", "title": "Minimal Dict"}
        task = Task.from_dict(data)

        assert task.id == "task_6"
        assert task.title == "Minimal Dict"
        assert task.description == ""
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.parent_id is None
        assert task.tags == []
        assert task.subtasks == []

    def test_task_roundtrip_to_dict_from_dict(self):
        """Test that to_dict and from_dict are inverses."""
        original = Task(
            id="task_7",
            title="Roundtrip",
            description="Test roundtrip",
            status=TaskStatus.BLOCKED,
            priority=TaskPriority.CRITICAL,
            parent_id="parent_4",
            tags=["roundtrip", "test"],
        )
        original.subtasks = ["sub_4", "sub_5"]

        data = original.to_dict()
        restored = Task.from_dict(data)

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.status == original.status
        assert restored.priority == original.priority
        assert restored.parent_id == original.parent_id
        assert restored.tags == original.tags
        assert restored.subtasks == original.subtasks

    def test_task_tags_default_empty_list(self):
        """Test that tags default to empty list, not None."""
        task = Task(id="task_8", title="Tags Test", tags=None)
        assert task.tags == []
        assert isinstance(task.tags, list)

    def test_task_subtasks_initialization(self):
        """Test that subtasks are initialized as empty list."""
        task = Task(id="task_9", title="Subtasks Test")
        assert task.subtasks == []
        assert isinstance(task.subtasks, list)


class TestTaskManager:
    """Tests for TaskManager class."""

    def test_task_manager_initialization_default(self, tmp_path):
        """Test TaskManager initialization with default storage path."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        assert manager.storage_path == tmp_path / "tasks.json"
        assert manager._tasks == {}

    def test_task_manager_initialization_creates_directory(self, tmp_path):
        """Test that TaskManager creates storage directory if needed."""
        storage_path = tmp_path / "subdir" / "tasks.json"
        manager = TaskManager(storage_path=storage_path)
        # Directory should be created on first save
        assert manager.storage_path == storage_path

    def test_task_manager_load_empty_file(self, tmp_path):
        """Test loading from non-existent file."""
        storage_path = tmp_path / "nonexistent.json"
        manager = TaskManager(storage_path=storage_path)
        assert manager._tasks == {}

    def test_task_manager_create_task_basic(self, tmp_path):
        """Test creating a basic task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="New Task")

        assert task.id is not None
        assert task.title == "New Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.id in manager._tasks

    def test_task_manager_create_task_full(self, tmp_path):
        """Test creating a task with all parameters."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(
            title="Full Task",
            description="Complete description",
            priority=TaskPriority.HIGH,
            tags=["urgent", "feature"],
        )

        assert task.title == "Full Task"
        assert task.description == "Complete description"
        assert task.priority == TaskPriority.HIGH
        assert task.tags == ["urgent", "feature"]

    def test_task_manager_create_task_with_parent(self, tmp_path):
        """Test creating a subtask with parent."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent = manager.create_task(title="Parent Task")
        child = manager.create_task(title="Child Task", parent_id=parent.id)

        assert child.parent_id == parent.id
        assert child.id in parent.subtasks
        assert child.id in manager._tasks[parent.id].subtasks

    def test_task_manager_get_task_exists(self, tmp_path):
        """Test getting an existing task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        created = manager.create_task(title="Get Task")
        retrieved = manager.get_task(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Get Task"

    def test_task_manager_get_task_not_exists(self, tmp_path):
        """Test getting a non-existent task returns None."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        result = manager.get_task("nonexistent_id")
        assert result is None

    def test_task_manager_update_task_status(self, tmp_path):
        """Test updating task status."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Status Task")
        original_updated_at = task.updated_at

        time.sleep(0.01)  # Ensure time difference
        result = manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)

        assert result is True
        updated_task = manager.get_task(task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.updated_at > original_updated_at

    def test_task_manager_update_task_status_nonexistent(self, tmp_path):
        """Test updating status of non-existent task returns False."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        result = manager.update_task_status("nonexistent", TaskStatus.COMPLETED)
        assert result is False

    def test_task_manager_list_tasks_all(self, tmp_path):
        """Test listing all tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        task3 = manager.create_task(title="Task 3")

        tasks = manager.list_tasks()
        assert len(tasks) == 3
        assert all(t.id in [task1.id, task2.id, task3.id] for t in tasks)

    def test_task_manager_list_tasks_by_status(self, tmp_path):
        """Test listing tasks filtered by status."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Pending Task")
        task2 = manager.create_task(title="Completed Task")
        manager.update_task_status(task2.id, TaskStatus.COMPLETED)

        pending = manager.list_tasks(status=TaskStatus.PENDING)
        completed = manager.list_tasks(status=TaskStatus.COMPLETED)

        assert len(pending) == 1
        assert pending[0].id == task1.id
        assert len(completed) == 1
        assert completed[0].id == task2.id

    def test_task_manager_list_tasks_by_parent(self, tmp_path):
        """Test listing tasks filtered by parent."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent1 = manager.create_task(title="Parent 1")
        parent2 = manager.create_task(title="Parent 2")
        child1 = manager.create_task(title="Child 1", parent_id=parent1.id)
        child2 = manager.create_task(title="Child 2", parent_id=parent1.id)
        child3 = manager.create_task(title="Child 3", parent_id=parent2.id)

        parent1_children = manager.list_tasks(parent_id=parent1.id)
        parent2_children = manager.list_tasks(parent_id=parent2.id)

        assert len(parent1_children) == 2
        assert all(t.parent_id == parent1.id for t in parent1_children)
        assert len(parent2_children) == 1
        assert parent2_children[0].parent_id == parent2.id

    def test_task_manager_list_tasks_root_only(self, tmp_path):
        """Test listing only root tasks (parent_id=None)."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        root1 = manager.create_task(title="Root 1")
        root2 = manager.create_task(title="Root 2")
        child = manager.create_task(title="Child", parent_id=root1.id)

        root_tasks = manager.list_tasks(parent_id=None)

        assert len(root_tasks) == 2
        assert all(t.parent_id is None for t in root_tasks)
        assert child.id not in [t.id for t in root_tasks]

    def test_task_manager_list_tasks_sorted_by_creation(self, tmp_path):
        """Test that list_tasks returns tasks sorted by creation time."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="First")
        time.sleep(0.01)
        task2 = manager.create_task(title="Second")
        time.sleep(0.01)
        task3 = manager.create_task(title="Third")

        tasks = manager.list_tasks()
        assert tasks[0].id == task1.id
        assert tasks[1].id == task2.id
        assert tasks[2].id == task3.id

    def test_task_manager_delete_task_simple(self, tmp_path):
        """Test deleting a simple task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Delete Me")

        result = manager.delete_task(task.id)

        assert result is True
        assert task.id not in manager._tasks
        assert manager.get_task(task.id) is None

    def test_task_manager_delete_task_nonexistent(self, tmp_path):
        """Test deleting non-existent task returns False."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        result = manager.delete_task("nonexistent")
        assert result is False

    def test_task_manager_delete_task_with_parent(self, tmp_path):
        """Test deleting a task removes it from parent's subtasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent = manager.create_task(title="Parent")
        child = manager.create_task(title="Child", parent_id=parent.id)

        assert child.id in manager.get_task(parent.id).subtasks

        manager.delete_task(child.id)

        assert child.id not in manager.get_task(parent.id).subtasks

    def test_task_manager_delete_task_orphan_subtasks(self, tmp_path):
        """Test deleting task orphans its subtasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent = manager.create_task(title="Parent")
        child1 = manager.create_task(title="Child 1", parent_id=parent.id)
        child2 = manager.create_task(title="Child 2", parent_id=parent.id)

        manager.delete_task(parent.id, delete_subtasks=False)

        assert manager.get_task(child1.id).parent_id is None
        assert manager.get_task(child2.id).parent_id is None

    def test_task_manager_delete_task_cascade(self, tmp_path):
        """Test deleting task with cascade deletes subtasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent = manager.create_task(title="Parent")
        child1 = manager.create_task(title="Child 1", parent_id=parent.id)
        child2 = manager.create_task(title="Child 2", parent_id=parent.id)

        manager.delete_task(parent.id, delete_subtasks=True)

        assert manager.get_task(parent.id) is None
        assert manager.get_task(child1.id) is None
        assert manager.get_task(child2.id) is None

    def test_task_manager_get_task_tree(self, tmp_path):
        """Test getting task tree structure."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        root1 = manager.create_task(title="Root 1")
        root2 = manager.create_task(title="Root 2")
        child1 = manager.create_task(title="Child 1", parent_id=root1.id)
        child2 = manager.create_task(title="Child 2", parent_id=root1.id)
        grandchild = manager.create_task(title="Grandchild", parent_id=child1.id)

        tree = manager.get_task_tree()

        assert len(tree) == 2
        assert tree[0]["id"] == root1.id
        assert len(tree[0]["children"]) == 2
        assert tree[0]["children"][0]["id"] == child1.id
        assert len(tree[0]["children"][0]["children"]) == 1
        assert tree[0]["children"][0]["children"][0]["id"] == grandchild.id

    def test_task_manager_persistence_save(self, tmp_path):
        """Test that tasks are persisted to file."""
        storage_path = tmp_path / "tasks.json"
        manager = TaskManager(storage_path=storage_path)
        task = manager.create_task(title="Persistent Task")

        assert storage_path.exists()
        with open(storage_path, "r") as f:
            data = json.load(f)
            assert task.id in data
            assert data[task.id]["title"] == "Persistent Task"

    def test_task_manager_persistence_load(self, tmp_path):
        """Test that tasks are loaded from file."""
        storage_path = tmp_path / "tasks.json"

        # Create and save tasks
        manager1 = TaskManager(storage_path=storage_path)
        task1 = manager1.create_task(title="Task 1")
        task2 = manager1.create_task(title="Task 2")

        # Load in new manager
        manager2 = TaskManager(storage_path=storage_path)

        assert len(manager2._tasks) == 2
        assert manager2.get_task(task1.id).title == "Task 1"
        assert manager2.get_task(task2.id).title == "Task 2"

    def test_task_manager_load_legacy_list_format(self, tmp_path):
        """Test loading legacy list format tasks."""
        storage_path = tmp_path / "tasks.json"

        # Create legacy format data
        legacy_data = [
            {
                "id": "legacy_1",
                "title": "Legacy Task",
                "status": "todo",
                "priority": "medium",
            },
            {
                "id": "legacy_2",
                "title": "Done Task",
                "status": "done",
                "priority": "low",
            },
        ]

        with open(storage_path, "w") as f:
            json.dump(legacy_data, f)

        manager = TaskManager(storage_path=storage_path)

        assert len(manager._tasks) == 2
        assert manager.get_task("legacy_1").status == TaskStatus.PENDING
        assert manager.get_task("legacy_2").status == TaskStatus.COMPLETED

    def test_task_manager_load_dict_format(self, tmp_path):
        """Test loading new dict format tasks."""
        storage_path = tmp_path / "tasks.json"

        # Create dict format data
        dict_data = {
            "task_1": {
                "id": "task_1",
                "title": "Dict Task 1",
                "status": "pending",
                "priority": "high",
            },
            "task_2": {
                "id": "task_2",
                "title": "Dict Task 2",
                "status": "completed",
                "priority": "low",
            },
        }

        with open(storage_path, "w") as f:
            json.dump(dict_data, f)

        manager = TaskManager(storage_path=storage_path)

        assert len(manager._tasks) == 2
        assert manager.get_task("task_1").title == "Dict Task 1"
        assert manager.get_task("task_2").title == "Dict Task 2"

    def test_task_manager_clear_all_tasks(self, tmp_path):
        """Test clearing all tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1")
        manager.create_task(title="Task 2")
        manager.create_task(title="Task 3")

        assert len(manager._tasks) == 3

        manager.clear_all_tasks()

        assert len(manager._tasks) == 0
        assert manager.list_tasks() == []

    def test_task_manager_multiple_status_transitions(self, tmp_path):
        """Test multiple status transitions on same task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Status Transitions")

        assert task.status == TaskStatus.PENDING

        manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)
        assert manager.get_task(task.id).status == TaskStatus.IN_PROGRESS

        manager.update_task_status(task.id, TaskStatus.BLOCKED)
        assert manager.get_task(task.id).status == TaskStatus.BLOCKED

        manager.update_task_status(task.id, TaskStatus.COMPLETED)
        assert manager.get_task(task.id).status == TaskStatus.COMPLETED

    def test_task_manager_complex_hierarchy(self, tmp_path):
        """Test complex task hierarchy with multiple levels."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")

        # Create hierarchy
        root = manager.create_task(title="Root")
        branch1 = manager.create_task(title="Branch 1", parent_id=root.id)
        branch2 = manager.create_task(title="Branch 2", parent_id=root.id)
        leaf1 = manager.create_task(title="Leaf 1", parent_id=branch1.id)
        leaf2 = manager.create_task(title="Leaf 2", parent_id=branch1.id)
        leaf3 = manager.create_task(title="Leaf 3", parent_id=branch2.id)

        tree = manager.get_task_tree()

        assert len(tree) == 1
        assert tree[0]["id"] == root.id
        assert len(tree[0]["children"]) == 2
        assert len(tree[0]["children"][0]["children"]) == 2
        assert len(tree[0]["children"][1]["children"]) == 1

    def test_task_manager_task_id_uniqueness(self, tmp_path):
        """Test that created task IDs are unique."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        ids = set()

        for i in range(100):
            task = manager.create_task(title=f"Task {i}")
            assert task.id not in ids
            ids.add(task.id)

        assert len(ids) == 100

    def test_task_manager_load_error_handling(self, tmp_path, caplog):
        """Test error handling when loading corrupted file."""
        storage_path = tmp_path / "tasks.json"

        # Create corrupted JSON
        with open(storage_path, "w") as f:
            f.write("{ invalid json }")

        manager = TaskManager(storage_path=storage_path)

        # Should handle error gracefully
        assert manager._tasks == {}

    def test_task_manager_save_creates_parent_directory(self, tmp_path):
        """Test that save creates parent directories."""
        storage_path = tmp_path / "deep" / "nested" / "dir" / "tasks.json"
        manager = TaskManager(storage_path=storage_path)
        manager.create_task(title="Test")

        assert storage_path.exists()
        assert storage_path.parent.exists()

    def test_task_manager_filter_by_status_and_parent(self, tmp_path):
        """Test filtering by both status and parent."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent = manager.create_task(title="Parent")
        child1 = manager.create_task(title="Child 1", parent_id=parent.id)
        child2 = manager.create_task(title="Child 2", parent_id=parent.id)

        manager.update_task_status(child1.id, TaskStatus.COMPLETED)

        # Filter by parent and status
        completed_children = manager.list_tasks(
            status=TaskStatus.COMPLETED, parent_id=parent.id
        )

        assert len(completed_children) == 1
        assert completed_children[0].id == child1.id

    def test_task_manager_empty_list_operations(self, tmp_path):
        """Test list operations on empty manager."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")

        assert manager.list_tasks() == []
        assert manager.list_tasks(status=TaskStatus.PENDING) == []
        assert manager.list_tasks(parent_id="nonexistent") == []
        assert manager.get_task_tree() == []

    def test_task_manager_subtask_tracking(self, tmp_path):
        """Test that subtask relationships are properly tracked."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent = manager.create_task(title="Parent")
        child1 = manager.create_task(title="Child 1", parent_id=parent.id)
        child2 = manager.create_task(title="Child 2", parent_id=parent.id)
        child3 = manager.create_task(title="Child 3", parent_id=parent.id)

        parent_task = manager.get_task(parent.id)
        assert len(parent_task.subtasks) == 3
        assert child1.id in parent_task.subtasks
        assert child2.id in parent_task.subtasks
        assert child3.id in parent_task.subtasks

    def test_task_manager_delete_with_orphaned_grandchildren(self, tmp_path):
        """Test deleting parent with grandchildren orphans them correctly."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        parent = manager.create_task(title="Parent")
        child = manager.create_task(title="Child", parent_id=parent.id)
        grandchild = manager.create_task(title="Grandchild", parent_id=child.id)

        manager.delete_task(parent.id, delete_subtasks=False)

        # Child should be orphaned
        assert manager.get_task(child.id).parent_id is None
        # Grandchild should still have child as parent
        assert manager.get_task(grandchild.id).parent_id == child.id

    def test_task_manager_persistence_with_complex_data(self, tmp_path):
        """Test persistence with complex task data."""
        storage_path = tmp_path / "tasks.json"

        # Create complex structure
        manager1 = TaskManager(storage_path=storage_path)
        root = manager1.create_task(
            title="Root",
            description="Root description",
            priority=TaskPriority.CRITICAL,
            tags=["important", "urgent"],
        )
        child = manager1.create_task(
            title="Child",
            description="Child description",
            priority=TaskPriority.HIGH,
            parent_id=root.id,
            tags=["feature"],
        )
        manager1.update_task_status(child.id, TaskStatus.IN_PROGRESS)

        # Load and verify
        manager2 = TaskManager(storage_path=storage_path)
        loaded_root = manager2.get_task(root.id)
        loaded_child = manager2.get_task(child.id)

        assert loaded_root.title == "Root"
        assert loaded_root.priority == TaskPriority.CRITICAL
        assert loaded_root.tags == ["important", "urgent"]
        assert loaded_child.status == TaskStatus.IN_PROGRESS
        assert loaded_child.parent_id == root.id


class TestTaskProgress:
    """Tests for task progress tracking."""

    def test_task_progress_initialization(self):
        """Test task progress initializes to 0."""
        task = Task(id="task_1", title="Progress Task")
        assert task.progress == 0

    def test_task_progress_custom_value(self):
        """Test task with custom progress value."""
        task = Task(id="task_2", title="Progress Task", progress=50)
        assert task.progress == 50

    def test_task_progress_clamping_upper(self):
        """Test progress is clamped to 100."""
        task = Task(id="task_3", title="Progress Task", progress=150)
        assert task.progress == 100

    def test_task_progress_clamping_lower(self):
        """Test progress is clamped to 0."""
        task = Task(id="task_4", title="Progress Task", progress=-50)
        assert task.progress == 0

    def test_update_task_progress(self, tmp_path):
        """Test updating task progress."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Progress Task")

        result = manager.update_task_progress(task.id, 75)
        assert result is True
        assert manager.get_task(task.id).progress == 75

    def test_update_task_progress_nonexistent(self, tmp_path):
        """Test updating progress of non-existent task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        result = manager.update_task_progress("nonexistent", 50)
        assert result is False

    def test_task_progress_persistence(self, tmp_path):
        """Test progress is persisted."""
        storage_path = tmp_path / "tasks.json"
        manager1 = TaskManager(storage_path=storage_path)
        task = manager1.create_task(title="Progress Task", progress=60)

        manager2 = TaskManager(storage_path=storage_path)
        loaded_task = manager2.get_task(task.id)
        assert loaded_task.progress == 60


class TestTaskOwnership:
    """Tests for task ownership."""

    def test_task_owner_initialization(self):
        """Test task owner initializes to None."""
        task = Task(id="task_1", title="Owner Task")
        assert task.owner is None

    def test_task_owner_custom_value(self):
        """Test task with custom owner."""
        task = Task(id="task_2", title="Owner Task", owner="alice")
        assert task.owner == "alice"

    def test_update_task_owner(self, tmp_path):
        """Test updating task owner."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Owner Task")

        result = manager.update_task_owner(task.id, "bob")
        assert result is True
        assert manager.get_task(task.id).owner == "bob"

    def test_update_task_owner_to_none(self, tmp_path):
        """Test clearing task owner."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Owner Task", owner="alice")

        result = manager.update_task_owner(task.id, None)
        assert result is True
        assert manager.get_task(task.id).owner is None

    def test_get_tasks_by_owner(self, tmp_path):
        """Test getting tasks by owner."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1", owner="alice")
        task2 = manager.create_task(title="Task 2", owner="bob")
        task3 = manager.create_task(title="Task 3", owner="alice")

        alice_tasks = manager.get_tasks_by_owner("alice")
        bob_tasks = manager.get_tasks_by_owner("bob")

        assert len(alice_tasks) == 2
        assert len(bob_tasks) == 1
        assert all(t.owner == "alice" for t in alice_tasks)
        assert all(t.owner == "bob" for t in bob_tasks)


class TestTaskMetadata:
    """Tests for task metadata."""

    def test_task_metadata_initialization(self):
        """Test task metadata initializes to empty dict."""
        task = Task(id="task_1", title="Metadata Task")
        assert task.metadata == {}

    def test_task_metadata_custom_value(self):
        """Test task with custom metadata."""
        metadata = {"key": "value", "count": 42}
        task = Task(id="task_2", title="Metadata Task", metadata=metadata)
        assert task.metadata == metadata

    def test_update_task_metadata(self, tmp_path):
        """Test updating task metadata."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Metadata Task")

        result = manager.update_task_metadata(task.id, {"key": "value"})
        assert result is True
        assert manager.get_task(task.id).metadata == {"key": "value"}

    def test_update_task_metadata_merge(self, tmp_path):
        """Test metadata update merges with existing."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Metadata Task", metadata={"a": 1})

        manager.update_task_metadata(task.id, {"b": 2})
        metadata = manager.get_task(task.id).metadata
        assert metadata == {"a": 1, "b": 2}

    def test_task_metadata_persistence(self, tmp_path):
        """Test metadata is persisted."""
        storage_path = tmp_path / "tasks.json"
        manager1 = TaskManager(storage_path=storage_path)
        task = manager1.create_task(
            title="Metadata Task",
            metadata={"custom": "data", "version": 1}
        )

        manager2 = TaskManager(storage_path=storage_path)
        loaded_task = manager2.get_task(task.id)
        assert loaded_task.metadata == {"custom": "data", "version": 1}


class TestTaskDependencies:
    """Tests for task dependencies (blocks/blockedBy)."""

    def test_task_dependencies_initialization(self):
        """Test task dependencies initialize to empty lists."""
        task = Task(id="task_1", title="Dependency Task")
        assert task.blocks == []
        assert task.blockedBy == []

    def test_add_task_dependency(self, tmp_path):
        """Test adding a task dependency."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")

        result = manager.add_task_dependency(task1.id, task2.id)
        assert result is True

        t1 = manager.get_task(task1.id)
        t2 = manager.get_task(task2.id)
        assert task2.id in t1.blocks
        assert task1.id in t2.blockedBy

    def test_add_task_dependency_nonexistent(self, tmp_path):
        """Test adding dependency with non-existent task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task = manager.create_task(title="Task")

        result = manager.add_task_dependency(task.id, "nonexistent")
        assert result is False

    def test_remove_task_dependency(self, tmp_path):
        """Test removing a task dependency."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")

        manager.add_task_dependency(task1.id, task2.id)
        result = manager.remove_task_dependency(task1.id, task2.id)
        assert result is True

        t1 = manager.get_task(task1.id)
        t2 = manager.get_task(task2.id)
        assert task2.id not in t1.blocks
        assert task1.id not in t2.blockedBy

    def test_get_blocked_tasks(self, tmp_path):
        """Test getting tasks blocked by a task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        task3 = manager.create_task(title="Task 3")

        manager.add_task_dependency(task1.id, task2.id)
        manager.add_task_dependency(task1.id, task3.id)

        blocked = manager.get_blocked_tasks(task1.id)
        assert len(blocked) == 2
        assert all(t.id in [task2.id, task3.id] for t in blocked)

    def test_get_blocking_tasks(self, tmp_path):
        """Test getting tasks that block a task."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        task3 = manager.create_task(title="Task 3")

        manager.add_task_dependency(task1.id, task3.id)
        manager.add_task_dependency(task2.id, task3.id)

        blocking = manager.get_blocking_tasks(task3.id)
        assert len(blocking) == 2
        assert all(t.id in [task1.id, task2.id] for t in blocking)

    def test_is_task_blocked_true(self, tmp_path):
        """Test checking if task is blocked."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")

        manager.add_task_dependency(task1.id, task2.id)
        assert manager.is_task_blocked(task2.id) is True

    def test_is_task_blocked_false_when_blocker_completed(self, tmp_path):
        """Test task is not blocked when blocker is completed."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")

        manager.add_task_dependency(task1.id, task2.id)
        manager.update_task_status(task1.id, TaskStatus.COMPLETED)
        assert manager.is_task_blocked(task2.id) is False

    def test_task_dependencies_persistence(self, tmp_path):
        """Test dependencies are persisted."""
        storage_path = tmp_path / "tasks.json"
        manager1 = TaskManager(storage_path=storage_path)
        task1 = manager1.create_task(title="Task 1")
        task2 = manager1.create_task(title="Task 2")
        manager1.add_task_dependency(task1.id, task2.id)

        manager2 = TaskManager(storage_path=storage_path)
        t1 = manager2.get_task(task1.id)
        t2 = manager2.get_task(task2.id)
        assert task2.id in t1.blocks
        assert task1.id in t2.blockedBy

    def test_delete_task_cleans_dependencies(self, tmp_path):
        """Test deleting task cleans up dependencies."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        task3 = manager.create_task(title="Task 3")

        manager.add_task_dependency(task1.id, task2.id)
        manager.add_task_dependency(task2.id, task3.id)

        manager.delete_task(task2.id)

        t1 = manager.get_task(task1.id)
        t3 = manager.get_task(task3.id)
        assert task2.id not in t1.blocks
        assert task2.id not in t3.blockedBy


class TestTaskFiltering:
    """Tests for advanced task filtering."""

    def test_list_tasks_by_priority(self, tmp_path):
        """Test filtering tasks by priority."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1", priority=TaskPriority.HIGH)
        task2 = manager.create_task(title="Task 2", priority=TaskPriority.LOW)
        task3 = manager.create_task(title="Task 3", priority=TaskPriority.HIGH)

        high_priority = manager.list_tasks(priority=TaskPriority.HIGH)
        assert len(high_priority) == 2
        assert all(t.priority == TaskPriority.HIGH for t in high_priority)

    def test_list_tasks_by_owner(self, tmp_path):
        """Test filtering tasks by owner."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1", owner="alice")
        task2 = manager.create_task(title="Task 2", owner="bob")
        task3 = manager.create_task(title="Task 3", owner="alice")

        alice_tasks = manager.list_tasks(owner="alice")
        assert len(alice_tasks) == 2
        assert all(t.owner == "alice" for t in alice_tasks)

    def test_list_tasks_by_tags(self, tmp_path):
        """Test filtering tasks by tags."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1", tags=["urgent", "bug"])
        task2 = manager.create_task(title="Task 2", tags=["feature"])
        task3 = manager.create_task(title="Task 3", tags=["urgent", "feature"])

        urgent_tasks = manager.list_tasks(tags=["urgent"])
        assert len(urgent_tasks) == 2

    def test_list_tasks_sort_by_priority(self, tmp_path):
        """Test sorting tasks by priority."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1", priority=TaskPriority.LOW)
        manager.create_task(title="Task 2", priority=TaskPriority.CRITICAL)
        manager.create_task(title="Task 3", priority=TaskPriority.MEDIUM)

        tasks = manager.list_tasks(sort_by="priority")
        assert tasks[0].priority == TaskPriority.CRITICAL
        assert tasks[1].priority == TaskPriority.MEDIUM
        assert tasks[2].priority == TaskPriority.LOW

    def test_list_tasks_sort_by_progress(self, tmp_path):
        """Test sorting tasks by progress."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1", progress=30)
        manager.create_task(title="Task 2", progress=100)
        manager.create_task(title="Task 3", progress=50)

        tasks = manager.list_tasks(sort_by="progress")
        assert tasks[0].progress == 30
        assert tasks[1].progress == 50
        assert tasks[2].progress == 100

    def test_list_tasks_multiple_filters(self, tmp_path):
        """Test filtering with multiple criteria."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(
            title="Task 1",
            priority=TaskPriority.HIGH,
            owner="alice"
        )
        task2 = manager.create_task(
            title="Task 2",
            priority=TaskPriority.HIGH,
            owner="bob"
        )
        task3 = manager.create_task(
            title="Task 3",
            priority=TaskPriority.LOW,
            owner="alice"
        )

        manager.update_task_status(task1.id, TaskStatus.IN_PROGRESS)
        manager.update_task_status(task3.id, TaskStatus.IN_PROGRESS)

        tasks = manager.list_tasks(
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            owner="alice"
        )
        assert len(tasks) == 1
        assert tasks[0].id == task1.id


class TestTaskQueries:
    """Tests for task query methods."""

    def test_get_high_priority_tasks(self, tmp_path):
        """Test getting high and critical priority tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1", priority=TaskPriority.CRITICAL)
        manager.create_task(title="Task 2", priority=TaskPriority.HIGH)
        manager.create_task(title="Task 3", priority=TaskPriority.MEDIUM)
        manager.create_task(title="Task 4", priority=TaskPriority.LOW)

        high_priority = manager.get_high_priority_tasks()
        assert len(high_priority) == 2

    def test_get_in_progress_tasks(self, tmp_path):
        """Test getting in-progress tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        manager.update_task_status(task1.id, TaskStatus.IN_PROGRESS)
        manager.update_task_status(task2.id, TaskStatus.COMPLETED)

        in_progress = manager.get_in_progress_tasks()
        assert len(in_progress) == 1
        assert in_progress[0].id == task1.id

    def test_get_blocked_tasks_list(self, tmp_path):
        """Test getting blocked tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        manager.update_task_status(task1.id, TaskStatus.BLOCKED)
        manager.update_task_status(task2.id, TaskStatus.PENDING)

        blocked = manager.get_blocked_tasks_list()
        assert len(blocked) == 1
        assert blocked[0].id == task1.id

    def test_get_completed_tasks(self, tmp_path):
        """Test getting completed tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        manager.update_task_status(task1.id, TaskStatus.COMPLETED)

        completed = manager.get_completed_tasks()
        assert len(completed) == 1
        assert completed[0].id == task1.id

    def test_get_pending_tasks(self, tmp_path):
        """Test getting pending tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        manager.update_task_status(task2.id, TaskStatus.IN_PROGRESS)

        pending = manager.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].id == task1.id

    def test_get_tasks_with_tag(self, tmp_path):
        """Test getting tasks with specific tag."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1", tags=["bug", "urgent"])
        manager.create_task(title="Task 2", tags=["feature"])
        manager.create_task(title="Task 3", tags=["bug", "feature"])

        bug_tasks = manager.get_tasks_with_tag("bug")
        assert len(bug_tasks) == 2

    def test_get_incomplete_tasks(self, tmp_path):
        """Test getting incomplete tasks."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        task3 = manager.create_task(title="Task 3")
        manager.update_task_status(task2.id, TaskStatus.COMPLETED)
        manager.update_task_status(task3.id, TaskStatus.CANCELLED)

        incomplete = manager.get_incomplete_tasks()
        assert len(incomplete) == 1
        assert incomplete[0].id == task1.id


class TestTaskStatistics:
    """Tests for task statistics."""

    def test_get_task_statistics_empty(self, tmp_path):
        """Test statistics on empty task list."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        stats = manager.get_task_statistics()

        assert stats["total"] == 0
        assert stats["average_progress"] == 0
        assert stats["blocked_count"] == 0

    def test_get_task_statistics_by_status(self, tmp_path):
        """Test statistics count by status."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        task3 = manager.create_task(title="Task 3")
        manager.update_task_status(task1.id, TaskStatus.COMPLETED)
        manager.update_task_status(task2.id, TaskStatus.IN_PROGRESS)

        stats = manager.get_task_statistics()
        assert stats["total"] == 3
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["in_progress"] == 1
        assert stats["by_status"]["completed"] == 1

    def test_get_task_statistics_by_priority(self, tmp_path):
        """Test statistics count by priority."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1", priority=TaskPriority.HIGH)
        manager.create_task(title="Task 2", priority=TaskPriority.HIGH)
        manager.create_task(title="Task 3", priority=TaskPriority.LOW)

        stats = manager.get_task_statistics()
        assert stats["by_priority"]["high"] == 2
        assert stats["by_priority"]["low"] == 1

    def test_get_task_statistics_by_owner(self, tmp_path):
        """Test statistics count by owner."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1", owner="alice")
        manager.create_task(title="Task 2", owner="alice")
        manager.create_task(title="Task 3", owner="bob")
        manager.create_task(title="Task 4")

        stats = manager.get_task_statistics()
        assert stats["by_owner"]["alice"] == 2
        assert stats["by_owner"]["bob"] == 1
        assert stats["by_owner"]["unassigned"] == 1

    def test_get_task_statistics_average_progress(self, tmp_path):
        """Test statistics average progress."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        manager.create_task(title="Task 1", progress=0)
        manager.create_task(title="Task 2", progress=50)
        manager.create_task(title="Task 3", progress=100)

        stats = manager.get_task_statistics()
        assert stats["average_progress"] == 50

    def test_get_task_statistics_blocked_count(self, tmp_path):
        """Test statistics blocked count."""
        manager = TaskManager(storage_path=tmp_path / "tasks.json")
        task1 = manager.create_task(title="Task 1")
        task2 = manager.create_task(title="Task 2")
        task3 = manager.create_task(title="Task 3")

        manager.add_task_dependency(task1.id, task2.id)
        manager.add_task_dependency(task1.id, task3.id)

        stats = manager.get_task_statistics()
        assert stats["blocked_count"] == 2
