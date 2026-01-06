import subprocess
import os

def read_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filepath: str, content: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def run_pylint(filepath: str) -> str:
    """Runs Pylint on the specific file and captures output."""
    try:
        # We use --errors-only or minimal reporting to keep tokens low
        result = subprocess.run(
            ["pylint", filepath, "--disable=C0111,C0103", "--score=n"], 
            capture_output=True, 
            text=True
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Tool Error: {str(e)}"

def run_pytest(test_path: str) -> dict:
    """Runs Pytest and returns success status."""
    try:
        result = subprocess.run(
            ["pytest", test_path], 
            capture_output=True, 
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr
        }
    except Exception as e:
        return {"success": False, "output": f"Tool Error: {str(e)}"}