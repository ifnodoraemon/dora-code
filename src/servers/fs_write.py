import os
from mcp.server.fastmcp import FastMCP
from src.core.security import validate_path

mcp = FastMCP("PolymathFileSystemWriter")

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write text content to a file."""
    valid_path = validate_path(path)
    try:
        os.makedirs(os.path.dirname(valid_path), exist_ok=True)
        with open(valid_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

if __name__ == "__main__":
    mcp.run()
