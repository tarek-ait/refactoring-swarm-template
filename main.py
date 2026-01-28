import argparse
import sys
import os
import glob
from dotenv import load_dotenv

# Loading .env first
load_dotenv()

from src.utils.logger import log_experiment, ActionType
from src.graph import app
from src.tools import read_file, write_file, initialize_sandbox

def main():
    # Argument Parsing (REQUIRED by Lab Statement)
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True, help="Path to the buggy code folder")
    args = parser.parse_args()

    target_dir = args.target_dir
    if not os.path.exists(target_dir):
        print(f"ERROR: Dossier {target_dir} introuvable.")
        sys.exit(1)

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
        if "test" in py_file: continue # Skipping test files themselves
        
        test_file = os.path.join(os.path.dirname(py_file), "test_" + os.path.basename(py_file))
        if not os.path.exists(test_file):
            test_file = os.path.join(os.path.dirname(py_file), "tests.py")
        
        if not os.path.exists(test_file):
            print(f"ATTENTION: No test found for {py_file}. Skipping.")
            continue

        print(f"\nON-GOING: Processing Pair: {py_file} + {test_file}")

        # Read file content - use absolute path and extract .content
        file_result = read_file(os.path.basename(py_file), sandbox)
        if not file_result.success:
            print(f"ERROR: Could not read {py_file}: {file_result.error}")
            continue
        
        code_content = file_result.content

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
            final_state = None
            
            for event in app.stream(initial_state, config=config):
                # Capture the latest state from each node
                for node_name, node_state in event.items():
                    if isinstance(node_state, dict):
                        if final_state is None:
                            final_state = initial_state.copy()
                        final_state.update(node_state)
                
                # Check if we should stop
                if final_state and final_state.get("is_success"):
                    break
            
            # Write the fixed code back to the file
            if final_state and final_state.get("code_content"):
                fixed_code = final_state["code_content"]
                write_result = write_file(os.path.basename(py_file), fixed_code, sandbox)
                
                if write_result.success:
                    print(f"FIXED: Written fixed code to {py_file}")
                else:
                    print(f"WARNING: Could not write fixed code: {write_result.error}")
            
            print(f"SUCCESS: Finished processing {py_file}")
            
        except Exception as e:
            print(f"ERROR: Critical Error on {py_file}: {e}")
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