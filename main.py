import argparse
import sys
import os
import glob
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType

from src.graph import app
from src.tools import read_file

load_dotenv()

def main():
    # Argument Parsing (REQUIRED by Lab Statement)
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True, help="Path to the buggy code folder")
    args = parser.parse_args()

    target_dir = args.target_dir
    if not os.path.exists(target_dir):
        print(f"❌ Dossier {target_dir} introuvable.")
        sys.exit(1)

    print(f"🚀 DEMARRAGE SUR : {target_dir}")
    log_experiment(ActionType.STARTUP, {"target": target_dir}, "INFO", "System", "System")

    # Identifying Files (Assumes structure: program.py and test_program.py)
    # For this lab, we look for pairs of .py files and their tests.
    python_files = glob.glob(os.path.join(target_dir, "*.py"))
    
    for py_file in python_files:
        if "test" in py_file: continue # Skipping test files themselves
        
        test_file = os.path.join(os.path.dirname(py_file), "test_" + os.path.basename(py_file))
        if not os.path.exists(test_file):
             # Trying alternate naming convention
             test_file = os.path.join(os.path.dirname(py_file), "tests.py")
        
        if not os.path.exists(test_file):
            print(f"⚠️ No test found for {py_file}. Skipping.")
            continue

        print(f"\n🔄 Processing Pair: {py_file} + {test_file}")

        # Initializing State
        initial_state = {
            "target_file": py_file,
            "test_file": test_file,
            "code_content": read_file(py_file),
            "pylint_report": "",
            "test_report": "",
            "iteration": 0,
            "is_success": False
        }

        # Running the Swarm
        try:
            for event in app.stream(initial_state):
                pass 
            print(f"✅ Finished processing {py_file}")
        except Exception as e:
            print(f"❌ Critical Error on {py_file}: {e}")
            log_experiment("System", "ERROR", ActionType.DEBUG, {"error": str(e)}, "FAILURE")

    print("✅ MISSION_COMPLETE")

if __name__ == "__main__":
    main()