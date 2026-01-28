import os
import re
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from mistralai import Mistral

from src.tools import (
    run_pylint,
    run_pytest,
    initialize_sandbox,
)
from src.utils.logger import log_experiment, ActionType

# Load environment variables
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_AGENT_ID = os.getenv("MISTRAL_MODEL")  # This is actually the Agent ID

if not MISTRAL_API_KEY:
    raise ValueError("❌ Missing MISTRAL_API_KEY in .env")

if not MISTRAL_AGENT_ID:
    raise ValueError("❌ Missing MISTRAL_MODEL (Agent ID) in .env")

# Initialize Mistral client
client = Mistral(api_key=MISTRAL_API_KEY)


def _chat(system_prompt: str, user_prompt: str) -> str:
    """
    Internal helper to query Mistral Agent with a combined prompt.
    Uses the Agents API instead of Chat API.
    """
    # Combine system and user prompts for the agent
    combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
    
    response = client.agents.complete(
        agent_id=MISTRAL_AGENT_ID,
        messages=[
            {"role": "user", "content": combined_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def _extract_code_from_response(response: str) -> str:
    """
    Extract Python code from LLM response, handling markdown code blocks.
    """
    # Try to find code in ```python ... ``` blocks
    pattern = r"```python\s*(.*?)\s*```"
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Try to find code in ``` ... ``` blocks
    pattern = r"```\s*(.*?)\s*```"
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # If no code blocks, return the response as-is (might be raw code)
    return response.strip()


def auditor_agent(state: dict) -> dict:
    """
    Analyzes code using static analysis (pylint) and runs tests.
    LangGraph node function - receives and returns state dict.
    """
    # Extract from state
    code = state.get("code_content", "")
    test_file = state.get("test_file", "")
    task_description = state.get("task_description", "Analyze code for bugs and quality issues")

    sandbox = initialize_sandbox("./sandbox")
    
    # Write code to temp file for analysis
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", dir="./sandbox") as tmp:
        tmp.write(code.encode("utf-8"))
        tmp_path = Path(tmp.name)

    # Run pylint analysis
    analysis = run_pylint(tmp_path, sandbox)
    
    # Run tests to find logical bugs
    test_result = None
    if test_file and os.path.exists(test_file):
        test_result = run_pytest(Path(test_file), sandbox)
    
    # Clean up temp file
    try:
        os.unlink(tmp_path)
    except:
        pass
    
    # Build result for logging
    pylint_issues = []
    if analysis.success and analysis.issues:
        pylint_issues = [issue.to_dict() for issue in analysis.issues]
    
    # Extract test information safely
    test_passed = None
    test_output = ""
    test_errors = ""
    
    if test_result:
        test_passed = test_result.all_tests_passed if test_result.success else False
        # Get failed test info
        if test_result.failed_tests:
            test_errors = "\n".join([
                f"FAILED: {ft.test_name} - {ft.error_message}" 
                for ft in test_result.failed_tests
            ])
        test_output = str(test_result.stats) if test_result.stats else ""
    
    result = {
        "pylint_issues": pylint_issues,
        "pylint_score": analysis.score if analysis.success else 0.0,
        "test_passed": test_passed,
        "test_output": test_output,
        "test_errors": test_errors,
    }
    
    # Determine status message
    if test_passed is None:
        test_status = "SKIPPED"
    elif test_passed:
        test_status = "PASSED"
    else:
        test_status = "FAILED"
    
    log_experiment(
        agent_name="Auditor",
        model_used=f"pylint+pytest (Agent: {MISTRAL_AGENT_ID})",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Analyzing code for task: {task_description}",
            "output_response": f"Pylint: {len(pylint_issues)} issues, score: {analysis.score}. Tests: {test_status}"
        },
        status="SUCCESS" if analysis.success else "FAILURE"
    )
    
    # Return state update
    return {
        "pylint_report": str(result),
        "iteration": state.get("iteration", 0) + 1
    }


def fixer_agent(state: dict) -> dict:
    """
    Uses Mistral Agent to fix logical bugs in code based on pylint report and test failures.
    LangGraph node function - receives and returns state dict.
    """
    # Extract from state
    code = state.get("code_content", "")
    pylint_report = state.get("pylint_report", "")
    test_file = state.get("test_file", "")
    
    # Read test file content for context
    test_content = ""
    if test_file and os.path.exists(test_file):
        try:
            with open(test_file, "r") as f:
                test_content = f.read()
        except Exception:
            pass

    # Build the prompt for the agent
    system_prompt = """You are an expert Python debugger. Your task is to fix bugs in Python code.

RULES:
1. Analyze the code, test failures, and pylint issues carefully
2. Fix ALL logical bugs, not just syntax issues
3. Return ONLY the fixed Python code, wrapped in ```python ``` code blocks
4. Do NOT add explanations outside the code block
5. Keep the same function signatures and docstrings
6. Fix common bugs like:
   - Off-by-one errors in loops (range should be inclusive when needed)
   - Wrong comparison operators (== vs !=, < vs <=)
   - Mutable default arguments (use None instead of [] or {})
   - Division errors (check divisor, use correct length)
   - Return value logic errors
   - Early returns that skip iterations
   - Incorrect initialization values (e.g., 0 for max when values can be negative)
"""

    user_prompt = f"""## BUGGY CODE:
```python
{code}
```

## TEST FILE (tests that should pass after fixing):
```python
{test_content}
```

## ANALYSIS REPORT:
{pylint_report}

Fix all the bugs in the code so that the tests pass. Return only the fixed code.
"""

    try:
        # Call Mistral Agent to fix the code
        response = _chat(system_prompt, user_prompt)
        fixed_code = _extract_code_from_response(response)
        
        # Validate we got actual code back
        if not fixed_code or len(fixed_code) < 10:
            log_experiment(
                agent_name="Fixer",
                model_used=MISTRAL_AGENT_ID,
                action=ActionType.FIX,
                details={
                    "input_prompt": f"Fixing code ({len(code)} chars)",
                    "output_response": "Agent returned empty or invalid code"
                },
                status="FAILURE"
            )
            return {"code_content": code}
        
        log_experiment(
            agent_name="Fixer",
            model_used=MISTRAL_AGENT_ID,
            action=ActionType.FIX,
            details={
                "input_prompt": f"Fixing code ({len(code)} chars) with {len(test_content)} chars of tests",
                "output_response": f"Generated fixed code ({len(fixed_code)} chars)"
            },
            status="SUCCESS"
        )
        
        return {"code_content": fixed_code}
        
    except Exception as e:
        log_experiment(
            agent_name="Fixer",
            model_used=MISTRAL_AGENT_ID,
            action=ActionType.FIX,
            details={
                "input_prompt": f"Fixing code ({len(code)} chars)",
                "output_response": f"Error: {str(e)}"
            },
            status="FAILURE"
        )
        return {"code_content": code}


def judge_agent(state: dict) -> dict:
    """
    Evaluates the fixed code by running tests and static analysis.
    LangGraph node function - receives and returns state dict.
    """
    # Extract from state
    fixed_code = state.get("code_content", "")
    target_file = state.get("target_file", "")
    test_file = state.get("test_file", "")
    task_description = state.get("task_description", "Evaluate fixed code")

    sandbox = initialize_sandbox("./sandbox")
    
    # Write fixed code to the actual target file (so tests can import it)
    if target_file:
        try:
            with open(target_file, "w") as f:
                f.write(fixed_code)
        except Exception as e:
            print(f"WARNING: Could not write to {target_file}: {e}")

    # Run tests
    test_passed = False
    test_output = ""
    
    if test_file and os.path.exists(test_file):
        test_result = run_pytest(Path(test_file), sandbox)
        test_passed = test_result.all_tests_passed if test_result.success else False
        
        # Build test output summary
        if test_result.success:
            test_output = f"Stats: {test_result.stats}"
            if test_result.failed_tests:
                failed_names = [ft.test_name for ft in test_result.failed_tests]
                test_output += f" | Failed: {failed_names}"
        else:
            test_output = test_result.error or "Test execution failed"
    
    # Run pylint on fixed code
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", dir="./sandbox") as tmp:
        tmp.write(fixed_code.encode("utf-8"))
        tmp_path = Path(tmp.name)
    
    analysis = run_pylint(tmp_path, sandbox)
    
    # Clean up temp file
    try:
        os.unlink(tmp_path)
    except:
        pass
    
    # Build result
    pylint_issues = []
    if analysis.success and analysis.issues:
        pylint_issues = [issue.to_dict() for issue in analysis.issues]
    
    result = {
        "score": analysis.score if analysis.success else 0.0,
        "issues": pylint_issues,
        "test_passed": test_passed,
        "test_output": test_output[:500],  # Truncate for logging
    }
    
    # Success if tests pass OR we've hit max iterations
    iteration = state.get("iteration", 0)
    is_success = test_passed or iteration >= 5
    
    status_msg = "TESTS PASSED ✅" if test_passed else f"TESTS FAILED (iteration {iteration}/5)"
    
    log_experiment(
        agent_name="Judge",
        model_used=f"pylint+pytest (Agent: {MISTRAL_AGENT_ID})",
        action=ActionType.DEBUG,
        details={
            "input_prompt": f"Evaluating fixed code for task: {task_description}",
            "output_response": f"{status_msg}. Pylint score: {result['score']}, Issues: {len(result['issues'])}"
        },
        status="SUCCESS" if test_passed else "FAILURE"
    )
    
    return {
        "test_report": str(result),
        "is_success": is_success
    }