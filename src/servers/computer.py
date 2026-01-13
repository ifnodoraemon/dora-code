import os
import sys
import subprocess
import tempfile
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PolymathComputer")

def _get_pypi_suggestions(query: str) -> str:
    """Internal helper to get suggestions when a package is not found."""
    try:
        url = f"https://pypi.org/search/?q={query}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return ""
        
        import re
        names = re.findall(r'<span class="package-snippet__name">(.*?)</span>', response.text)
        descs = re.findall(r'<p class="package-snippet__description">(.*?)</p>', response.text)
        
        suggestions = []
        for i in range(min(3, len(names))):
            # Clean up tags if any
            name = names[i].replace('"', '')
            desc = descs[i].strip()
            suggestions.append(f"- **{name}**: {desc}")
        
        if suggestions:
            return "\n\nI couldn't find that exact package, but here are some similar ones on PyPI:\n" + "\n".join(suggestions)
        return ""
    except:
        return ""

@mcp.tool()
def list_installed_packages() -> str:
    """List all currently installed Python packages and their versions."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error listing packages: {str(e)}"

@mcp.tool()
def install_package(package_name: str) -> str:
    """
    Install a Python package using pip.
    If the package name is incorrect, I will provide suggestions based on PyPI search.
    """
    print(f"Attempting to install: {package_name}")
    try:
        # First, check if package exists to provide better feedback
        check_url = f"https://pypi.org/pypi/{package_name}/json"
        check_resp = requests.get(check_url, timeout=5)
        
        if check_resp.status_code != 200:
            error_msg = f"❌ Package '{package_name}' not found on PyPI."
            suggestions = _get_pypi_suggestions(package_name)
            return error_msg + suggestions + "\n\nPlease review the suggestions and try again with the correct name."

        # Package exists, proceed with installation
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return f"✅ Successfully installed {package_name}."
        else:
            return f"❌ Failed to install {package_name}.\nError: {result.stderr}"
            
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def execute_python(code: str) -> str:
    """
    Execute arbitrary Python code and return stdout/stderr.
    Useful for calculations, data analysis, or generating charts.
    
    The code runs in a temporary environment. 
    Images generated (e.g. via matplotlib) should be saved to 'drafts/'.
    """
    print(f"Executing Code:\n{code}")
    
    # 创建临时文件来存放代码
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        script_path = f.name

    try:
        # 使用当前的 Python 环境执行，这样可以使用已安装的库 (pandas, matplotlib等)
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30  # 防止死循环
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[Stderr]:\n{result.stderr}"
            
        return output if output.strip() else "Code executed successfully (no output)."
        
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30s limit)."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        # 清理临时文件
        if os.path.exists(script_path):
            os.remove(script_path)

if __name__ == "__main__":
    mcp.run()