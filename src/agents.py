import time
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.utils.logger import log_experiment, ActionType # MANDATORY IMPORT
from src.tools import write_file, run_pylint, run_pytest

load_dotenv()

# Ensure GOOGLE_API_KEY is set
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY environment variable. Set GOOGLE_API_KEY and retry.")

# Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0,
    google_api_key=GOOGLE_API_KEY,
)

def clean_code(text: str) -> str:
    if "```" in text:
        return text.split("```")[1].replace("python", "").strip()
    return text.strip()

# AGENT 1: THE AUDITOR (Static Analysis)
def auditor_agent(state):
    print(f"\n🧐 AUDITOR: Analyzing {state['target_file']}...")
    
    # Tool Execution
    lint_report = run_pylint(state["target_file"])
    
    # LLM Analysis
    prompt = f"""
    You are a Python Code Auditor. Analyze this code and the Pylint report.
    CODE:
    {state['code_content']}
    
    PYLINT REPORT:
    {lint_report}
    
    Provide a concise refactoring plan to fix errors and improve quality.
    """
    
    response = llm.invoke(prompt).content
    
    # MANDATORY LOGGING
    log_experiment(
        agent_name="Auditor",
        model_used="gemini-2.0-flash-lite",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": prompt,
            "output_response": response,
            "file": state["target_file"]
        },
        status="SUCCESS"
    )
    
    return {"pylint_report": response}

# AGENT 2: THE FIXER (Refactoring)
def fixer_agent(state):
    print(f"\n🔧 FIXER: Applying corrections (Iter {state['iteration']})...")
    
    # LLM Generation
    prompt = f"""
    You are a Senior Python Developer. Fix the code based on the Auditor's plan and the Test failures.
    
    ORIGINAL CODE:
    {state['code_content']}
    
    AUDITOR PLAN:
    {state['pylint_report']}
    
    TEST FAILURES (if any):
    {state.get('test_report', 'None yet')}
    
    Output ONLY the full fixed Python code inside markdown blocks.
    """
    
    response = llm.invoke(prompt).content
    fixed_code = clean_code(response)
    
    # Apply Fix (Toolsmith)
    write_file(state["target_file"], fixed_code)
    
    # MANDATORY LOGGING
    log_experiment(
        agent_name="Fixer",
        model_used="gemini-2.0-flash-lite",
        action=ActionType.FIX,
        details={
            "input_prompt": prompt,
            "output_response": response,
            "applied_changes": "Overwrote file content"
        },
        status="SUCCESS"
    )
    
    return {"code_content": fixed_code, "iteration": state["iteration"] + 1}

# AGENT 3: THE JUDGE (Testing)
def judge_agent(state):
    print(f"\n⚖️ JUDGE: Running tests on {state['test_file']}...")
    
    # Run Tests
    test_result = run_pytest(state["test_file"])
    
    # MANDATORY LOGGING
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