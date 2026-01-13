from mcp.server.fastmcp import FastMCP
from src.services.task_manager import TaskManager

mcp = FastMCP("PolymathTaskServer")
manager = TaskManager()

@mcp.tool()
def add_task(title: str, description: str = "", parent_id: str = None) -> str:
    """
    Add a new task to the project plan.
    
    Args:
        title: Short title of the task
        description: Detailed description
        parent_id: Optional ID of a parent task to create a sub-task
    """
    task_id = manager.add_task(title, description, parent_id)
    if task_id.startswith("Error"):
        return task_id
    return f"Task added. ID: {task_id}"

@mcp.tool()
def add_subtask(parent_id: str, title: str, description: str = "") -> str:
    """
    Dynamically add a SUB-TASK to a running Main Task.
    Use this WHENEVER you discover a specific step that needs to be done to complete the Main Task.
    
    Args:
        parent_id: The ID of the Main Task this belongs to.
        title: Short title (e.g., "Fix logic in auth.py")
        description: Details
    """
    return add_task(title, description, parent_id)

@mcp.tool()
def update_task_status(task_id: str, status: str) -> str:
    """
    Update the status of a task.
    
    Args:
        task_id: The ID of the task
        status: 'todo', 'in_progress', or 'done'
    """
    return manager.update_status(task_id, status)

@mcp.tool()
def list_tasks() -> str:
    """
    Show the current project task tree.
    Use this to review progress and decide what to do next.
    """
    return manager.get_task_tree()

if __name__ == "__main__":
    mcp.run()
