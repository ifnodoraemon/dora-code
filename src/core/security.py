import os

def validate_path(path: str, base_dir: str = None) -> str:
    """
    Validate that path is within the workspace sandbox.
    Defaults to current working directory if base_dir is not provided.
    
    Returns:
        The absolute path if valid.
    
    Raises:
        PermissionError: If path is outside sandbox.
    """
    if base_dir is None:
        base_dir = os.getcwd()
        
    abs_path = os.path.abspath(path)
    abs_base = os.path.abspath(base_dir)
    
    if not abs_path.startswith(abs_base):
        raise PermissionError(f"Access Denied: Path {path} is outside of the workspace sandbox ({abs_base}).")
        
    return abs_path
