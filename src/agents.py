import os
import time
from mistralai import Mistral
from src.utils.logger import log_experiment, ActionType
from src.tools import write_file, run_pylint, run_pytest

# --- MISTRAL SETUP ---
api_key = os.environ.get("MISTRAL_API_KEY")
agent_id = os.environ.get("MISTRAL_AGENT_ID")

if not api_key or not agent_id:
    raise ValueError("❌ Missing MISTRAL_API_KEY or MISTRAL_AGENT_ID in .env")

client = Mistral(api_key=api_key)

def call_mistral_agent(prompt: str) -> str:
    """Helper to call the specific Mistral Agent."""
    try:
        response = client.agents.complete(
            agent_id=agent_id,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Mistral API Error: {str(e)}"

def clean_code(text: str) -> str:
    """Extracts code from Markdown blocks if present."""
    if "```" in text:
        # Split by ``` and take the second part (the code)
        # Handles ```python and just ```
        parts = text.split("```")
        if len(parts) >= 2:
            return parts[1].replace("python", "").replace("python", "").strip()
    return text.strip()

# --- AGENT 1: THE AUDITOR (Static Analysis) ---
def auditor_agent(state):
    print(f"\n🧐 AUDITOR: Analyzing {state['target_file']}...")
    
    # 1. Tool Execution
    lint_report = run_pylint(state["target_file"])
    
    # 2. Mistral Analysis
    prompt = f"""
    Analyze this code and the Pylint report.
    
    CODE:
    {state['code_content']}
    
    PYLINT REPORT:
    {lint_report}
    
    Provide a concise refactoring plan to fix errors and improve quality.
    """
    
    response = call_mistral_agent(prompt)
    
    # 3. Logging
    log_experiment(
        agent_name="Auditor",
        model_used=agent_id, # Log the specific Agent ID
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": prompt,
            "output_response": response,
            "file": state["target_file"]
        },
        status="SUCCESS"
    )
    
    return {"pylint_report": response}

# --- AGENT 2: THE FIXER (Refactoring) ---
def fixer_agent(state):
    print(f"\n🔧 FIXER: Applying corrections (Iter {state['iteration']})...")
    
    # 1. Mistral Generation
    prompt = f"""
    Fix the code based on the Auditor's plan and the Test failures.
    
    ORIGINAL CODE:
    {state['code_content']}
    
    AUDITOR PLAN:
    {state['pylint_report']}
    
    TEST FAILURES:
    {state.get('test_report', 'None yet')}
    
    Output ONLY the full fixed Python code inside markdown blocks.
    """
    
    response = call_mistral_agent(prompt)
    fixed_code = clean_code(response)
    
    # 2. Apply Fix
    write_file(state["target_file"], fixed_code)
    
    # 3. Logging
    log_experiment(
        agent_name="Fixer",
        model_used=agent_id,
        action=ActionType.FIX,
        details={
            "input_prompt": prompt,
            "output_response": response,
            "applied_changes": "Overwrote file content"
        },
        status="SUCCESS"
    )
    
    return {"code_content": fixed_code, "iteration": state["iteration"] + 1}

# --- AGENT 3: THE JUDGE (Testing) ---
# The Judge uses Pytest, so it remains independent of the LLM.
def judge_agent(state):
    print(f"\n⚖️ JUDGE: Running tests on {state['test_file']}...")
    
    test_result = run_pytest(state["test_file"])
    
    log_experiment(
        agent_name="Judge",
        model_used="System-Pytest",
        action=ActionType.DEBUG,
        details={
            "input_prompt": f"Run pytest on {state['test_file']}",
            "output_response": test_result["output"],
            "passed": test_result["success"]
        },
        status="SUCCESS" if test_result["success"] else "FAILURE"
    )
    
    if test_result["success"]:
        print("✅ JUDGE: Tests Passed!")
        return {"is_success": True, "test_report": "ALL TESTS PASSED"}
    else:
        print("❌ JUDGE: Tests Failed.")
        return {"is_success": False, "test_report": test_result["output"]}