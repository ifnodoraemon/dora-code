import json
import os
import time
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field

TASKS_FILE = ".polymath/tasks.json"

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: str  # "todo", "in_progress", "done"
    parent_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    subtasks: List['Task'] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "subtasks": [t.to_dict() for t in self.subtasks]
        }

class TaskManager:
    def __init__(self, file_path: str = TASKS_FILE):
        self.file_path = file_path
        self.tasks: List[Task] = []
        self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            self.tasks = []
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Reconstruct Task objects (flat list internally for easier ID lookup, or tree?)
            # Let's keep a flat list in memory for easier management, build tree on export
            self.tasks = data # Assuming simple list of dicts for storage
        except Exception:
            self.tasks = []

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)

    def add_task(self, title: str, description: str = "", parent_id: Optional[str] = None) -> str:
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "description": description,
            "status": "todo",
            "parent_id": parent_id,
            "created_at": time.time()
        }
        
        # Verify parent exists
        if parent_id:
            parent = next((t for t in self.tasks if t["id"] == parent_id), None)
            if not parent:
                return "Error: Parent task ID not found."
            # Maybe update parent status to in_progress?
        
        self.tasks.append(new_task)
        self._save()
        return new_task["id"]

    def update_status(self, task_id: str, status: str) -> str:
        if status not in ["todo", "in_progress", "done"]:
            return "Error: Invalid status. Use 'todo', 'in_progress', or 'done'."
            
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return f"Error: Task {task_id} not found."
            
        task["status"] = status
        
        # Auto-update parent if all children are done? 
        # For now, keep it simple.
        
        self._save()
        return f"Task {task_id} updated to {status}."

    def get_task_tree(self) -> str:
        """Render a text-based tree of tasks."""
        if not self.tasks:
            return "No tasks found."

        # Build tree structure
        tree_map = {t["id"]: {**t, "children": []} for t in self.tasks}
        roots = []
        
        for t in self.tasks:
            if t["parent_id"] and t["parent_id"] in tree_map:
                tree_map[t["parent_id"]]["children"].append(tree_map[t["id"]])
            else:
                roots.append(tree_map[t["id"]])

        output = []
        
        def render_node(node, depth=0):
            icon = "☐" if node["status"] == "todo" else ("⏳" if node["status"] == "in_progress" else "✅")
            indent = "  " * depth
            output.append(f"{indent}{icon} [{node['id']}] {node['title']}")
            if node["description"]:
                output.append(f"{indent}    Full Description: {node['description']}")
            
            for child in node["children"]:
                render_node(child, depth + 1)

        output.append("=== Project Tasks ===")
        for root in roots:
            render_node(root)
            
        return "\n".join(output)
