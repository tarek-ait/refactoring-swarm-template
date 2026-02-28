import argparse
import sys
import os
import glob
import shutil
from datetime import datetime
from dotenv import load_dotenv

# ── ANSI Colors ────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
# ───────────────────────────────────────────────────────────────

# Loading .env first
load_dotenv()

from src.utils.logger import log_experiment, ActionType
from src.graph import app
from src.tools import read_file, initialize_sandbox

def main():
    # Argument Parsing (REQUIRED by Lab Statement)
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True, help="Path to the buggy code folder")
    args = parser.parse_args()

    target_dir = args.target_dir
    if not os.path.exists(target_dir):
        print(f"{BOLD}{RED}ERROR:{RESET} Dossier {target_dir} introuvable.")
        sys.exit(1)

    # Create backup folder within sandbox
    backup_dir = os.path.join(target_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)

    # Initialize sandbox BEFORE any file operations
    sandbox = initialize_sandbox(target_dir)

    print(f"\n{BOLD}{CYAN}{'━'*60}{RESET}")
    print(f"{BOLD}{CYAN}  REFACTORING SWARM  ->  {target_dir}{RESET}")
    print(f"{BOLD}{CYAN}{'━'*60}{RESET}\n")
    log_experiment(
        "System",
        "System",
        ActionType.DEBUG,
        {"target": target_dir, "input_prompt": "startup", "output_response": "initialized"},
        "SUCCESS"
    )

    # Identifying Files (Assumes structure: program.py and test_program.py)
    python_files = glob.glob(os.path.join(target_dir, "*.py"))
    
    for py_file in python_files:
        basename = os.path.basename(py_file)
        if basename.startswith("test_") or basename == "tests.py": 
            continue  # Skipping test files themselves
        
        test_file = os.path.join(os.path.dirname(py_file), "test_" + os.path.basename(py_file))
        if not os.path.exists(test_file):
            test_file = os.path.join(os.path.dirname(py_file), "tests.py")
        
        if not os.path.exists(test_file):
            print(f"{YELLOW}WARNING: No test found for {BOLD}{py_file}{RESET}{YELLOW}. Skipping.{RESET}")
            continue

        print(f"\n{BOLD}{BLUE}┌─ Processing:{RESET} {WHITE}{py_file}{RESET}")
        print(f"{BOLD}{BLUE}└─ Tests:     {RESET} {WHITE}{test_file}{RESET}")

        # Read file content directly
        try:
            with open(py_file, "r") as f:
                code_content = f.read()
        except Exception as e:
            print(f"{RED}ERROR: Could not read {py_file}: {e}{RESET}")
            continue

        # Create backup before processing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{os.path.basename(py_file)}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy(py_file, backup_path)
        print(f"  {DIM}Backup -> {backup_path}{RESET}")

        original_hash = hash(code_content)

        # Initializing State
        initial_state = {
            "target_file": py_file,
            "test_file": test_file,
            "code_content": code_content,
            "task_description": f"Analyze and fix bugs in {os.path.basename(py_file)}",
            "pylint_report": "",
            "test_report": "",
            "iteration": 0,
            "is_success": False
        }

        # Running the Swarm
        try:
            config = {"recursion_limit": 50}
            final_state = initial_state.copy()
            
            for event in app.stream(initial_state, config=config):
                # Capture the latest state from each node
                for node_name, node_state in event.items():
                    if isinstance(node_state, dict):
                        # Update final_state with new values
                        for key, value in node_state.items():
                            final_state[key] = value
                        
                        # Log iteration progress
                        if "iteration" in node_state:
                            it = final_state.get('iteration', 0)
                            bar = ("█" * it) + ("░" * (5 - it))
                            print(f"  {BOLD}{MAGENTA}↳ Iteration {it}/5{RESET}  {MAGENTA}{bar}{RESET}")
                        
                        # DEBUG: Show if code changed after fixer
                        if node_name == "fixer" and "code_content" in node_state:
                            new_hash = hash(node_state["code_content"])
                            if new_hash != original_hash:
                                print(f"    {YELLOW}Fixer modified code{RESET}")
                            else:
                                print(f"    {DIM}Fixer returned same code{RESET}")
                
                # Check if we should stop
                if final_state.get("is_success"):
                    test_report = str(final_state.get("test_report", ""))
                    if "'test_passed': True" in test_report:
                        print(f"  {BOLD}{GREEN}Tests passed!{RESET}")
                    else:
                        print(f"  {YELLOW}Max iterations reached, tests may still fail{RESET}")
                    break
            
            # Write the final fixed code back to the file
            fixed_code = final_state.get("code_content", "")
            
            if fixed_code and fixed_code.strip() != code_content.strip():
                with open(py_file, "w") as f:
                    f.write(fixed_code)
                print(f"  {CYAN}Written fixed code -> {py_file}{RESET}")
                # Show a compact diff of what changed
                import difflib
                original_lines = code_content.splitlines(keepends=True)
                fixed_lines = fixed_code.splitlines(keepends=True)
                diff = list(difflib.unified_diff(original_lines, fixed_lines, lineterm=""))
                changed = [l for l in diff if l.startswith(("+", "-")) and not l.startswith(("++", "--"))]
                if changed:
                    print(f"  {BOLD}Changes ({len(changed)} lines):{RESET}")
                    for line in changed[:20]:
                        if line.startswith("+"):
                            print(f"  {GREEN}  + {line[1:].rstrip()}{RESET}")
                        else:
                            print(f"  {RED}  - {line[1:].rstrip()}{RESET}")
            else:
                print(f"  {DIM}  No changes made to {py_file}{RESET}")
            
            print(f"\n{BOLD}{GREEN}SUCCESS:{RESET} Finished processing {WHITE}{py_file}{RESET}")
            
        except Exception as e:
            print(f"{BOLD}{RED}ERROR: Critical Error on {py_file}: {e}{RESET}")
            import traceback
            traceback.print_exc()
            log_experiment(
                "System",
                "Unknown",
                ActionType.DEBUG,
                {"error": str(e), "input_prompt": "error_handler", "output_response": str(e)},
                "FAILURE"
            )

    print(f"\n{BOLD}{GREEN}{'━'*60}{RESET}")
    print(f"{BOLD}{GREEN}  MISSION COMPLETE{RESET}")
    print(f"{BOLD}{GREEN}{'━'*60}{RESET}\n")

if __name__ == "__main__":
    main()