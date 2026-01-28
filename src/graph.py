from langgraph.graph import StateGraph, END
from .state import SwarmState
from .agents import auditor_agent, fixer_agent, judge_agent

def router(state: dict) -> str:
    """Decide whether to continue or end the workflow."""
    if state.get("is_success", False):
        return "end"
    if state.get("iteration", 0) > 5:  # Specified safety limit
        print("ATTENTION: Max iterations reached. Stopping.")
        return "end"
    return "auditor"  # Looping back to start

# Init Graph Definition
workflow = StateGraph(SwarmState)

# Adding Nodes
workflow.add_node("auditor", auditor_agent)
workflow.add_node("fixer", fixer_agent)
workflow.add_node("judge", judge_agent)

# Adding Edges
workflow.set_entry_point("auditor")
workflow.add_edge("auditor", "fixer")
workflow.add_edge("fixer", "judge")
workflow.add_conditional_edges(
    "judge",
    router,
    {
        "end": END,       # String key maps to END constant
        "auditor": "auditor"
    }
)

app = workflow.compile()