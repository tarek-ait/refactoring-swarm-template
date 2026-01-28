import argparse
import sys
import os
import glob
import shutil
from datetime import datetime
from dotenv import load_dotenv

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
        print(f"ERROR: Dossier {target_dir} introuvable.")
        sys.exit(1)

    # Create backup folder within sandbox
    backup_dir = os.path.join(target_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)

    # Initialize sandbox BEFORE any file operations
    sandbox = initialize_sandbox(target_dir)

    print(f"LAUNCHING: DEMARRAGE SUR : {target_dir}")
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
        if "test" in py_file: 
            continue  # Skipping test files themselves
        
        test_file = os.path.join(os.path.dirname(py_file), "test_" + os.path.basename(py_file))
        if not os.path.exists(test_file):
            test_file = os.path.join(os.path.dirname(py_file), "tests.py")
        
        if not os.path.exists(test_file):
            print(f"ATTENTION: No test found for {py_file}. Skipping.")
            continue

        print(f"\nON-GOING: Processing Pair: {py_file} + {test_file}")

        # Read file content directly
        try:
            with open(py_file, "r") as f:
                code_content = f.read()
        except Exception as e:
            print(f"ERROR: Could not read {py_file}: {e}")
            continue

        # Create backup before processing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{os.path.basename(py_file)}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy(py_file, backup_path)
        print(f"  Backup created: {backup_path}")

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
                            print(f"  ↳ Iteration {final_state.get('iteration', 0)}/5")
                        
                        # DEBUG: Show if code changed after fixer
                        if node_name == "fixer" and "code_content" in node_state:
                            new_hash = hash(node_state["code_content"])
                            if new_hash != original_hash:
                                print(f"    Fixer modified code")
                            else:
                                print(f"    Fixer returned same code")
                
                # Check if we should stop
                if final_state.get("is_success"):
                    test_report = str(final_state.get("test_report", ""))
                    if "'test_passed': True" in test_report:
                        print(f"  Tests passed!")
                    else:
                        print(f"  Max iterations reached, tests may still fail")
                    break
            
            # Write the final fixed code back to the file
            fixed_code = final_state.get("code_content", "")
            
            if fixed_code and fixed_code.strip() != code_content.strip():
                with open(py_file, "w") as f:
                    f.write(fixed_code)
                print(f"  Written fixed code to {py_file}")
            else:
                print(f"  No changes made to {py_file}")
            
            print(f"SUCCESS: Finished processing {py_file}")
            
        except Exception as e:
            print(f"ERROR: Critical Error on {py_file}: {e}")
            import traceback
            traceback.print_exc()
            log_experiment(
                "System",
                "Unknown",
                ActionType.DEBUG,
                {"error": str(e), "input_prompt": "error_handler", "output_response": str(e)},
                "FAILURE"
            )

    print("MISSION_COMPLETE")

if __name__ == "__main__":
    main()