"""
=============================================================================
TEST 10: Graph Workflow — Simulation
=============================================================================
Tests the LangGraph workflow definition: node registration, edge routing,
and the conditional router logic — WITHOUT calling the LLM.

Run:  python -m pytest tests/test_graph.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import router


class TestRouter:
    """Test the conditional routing logic."""

    def test_routes_to_end_on_success(self):
        state = {"is_success": True, "iteration": 1}
        assert router(state) == "end"
        print("  ✅ is_success=True → 'end'")

    def test_routes_to_end_on_max_iterations(self):
        state = {"is_success": False, "iteration": 6}
        assert router(state) == "end"
        print("  ✅ iteration=6 (>5) → 'end'")

    def test_routes_to_auditor_on_failure(self):
        state = {"is_success": False, "iteration": 2}
        assert router(state) == "auditor"
        print("  ✅ is_success=False, iter=2 → 'auditor' (loop back)")

    def test_routes_to_auditor_on_first_iteration(self):
        state = {"is_success": False, "iteration": 0}
        assert router(state) == "auditor"
        print("  ✅ Initial state → 'auditor'")

    def test_routes_to_end_at_boundary(self):
        """iteration > 5 is the condition, so iteration=5 should NOT end."""
        state = {"is_success": False, "iteration": 5}
        assert router(state) == "auditor"
        print("  ✅ iteration=5 (<=5) → 'auditor' (still one more try)")

    def test_routes_to_end_at_boundary_plus_one(self):
        state = {"is_success": False, "iteration": 6}
        assert router(state) == "end"
        print("  ✅ iteration=6 (>5) → 'end'")

    def test_missing_keys_default_to_continue(self):
        """Missing keys should default to safe values and continue."""
        state = {}
        result = router(state)
        assert result == "auditor"
        print("  ✅ Empty state → 'auditor' (safe default)")


class TestWorkflowStructure:
    """Test that the compiled graph has the expected structure."""

    def test_app_is_compiled(self):
        from src.graph import app
        assert app is not None
        print("  ✅ LangGraph app compiled successfully")

    def test_graph_has_nodes(self):
        from src.graph import workflow
        # The workflow object should have our three nodes
        # Access the internal nodes dict
        node_names = list(workflow.nodes.keys())
        assert "auditor" in node_names
        assert "fixer" in node_names
        assert "judge" in node_names
        print(f"  ✅ Graph nodes: {node_names}")
