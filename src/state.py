from typing import TypedDict, Optional

class SwarmState(TypedDict):
    target_file: str        # Path to the file being fixed
    test_file: str          # Path to the corresponding test file
    code_content: str       # Current content of the code
    pylint_report: str      # Output from The Auditor
    test_report: str        # Output from The Judge
    iteration: int          # Loop counter
    is_success: bool        # Flag to stop the swarm