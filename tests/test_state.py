"""
=============================================================================
TEST 9: State Schema — Simulation
=============================================================================
Tests the SwarmState TypedDict to verify it holds all the fields the
graph/agents expect, and that state flows work correctly.

Run:  python -m pytest tests/test_state.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state import SwarmState


class TestSwarmState:
    """Test the SwarmState TypedDict schema."""

    def test_all_required_fields_exist(self):
        """SwarmState should have all the expected keys."""
        expected_keys = [
            "target_file", "test_file", "code_content",
            "pylint_report", "test_report", "iteration",
            "is_success", "task_description"
        ]
        annotations = SwarmState.__annotations__
        for key in expected_keys:
            assert key in annotations, f"Missing key: {key}"
        print(f"  ✅ All {len(expected_keys)} fields present: {list(annotations.keys())}")

    def test_can_create_valid_state(self):
        """Should be able to create a valid state dict."""
        state: SwarmState = {
            "target_file": "./sandbox/bad_calc.py",
            "test_file": "./sandbox/test_bad_calc.py",
            "code_content": "def add(a, b): return a + b",
            "pylint_report": "",
            "test_report": "",
            "iteration": 0,
            "is_success": False,
            "task_description": "Fix bugs in bad_calc.py"
        }
        assert state["iteration"] == 0
        assert state["is_success"] is False
        assert state["target_file"].endswith("bad_calc.py")
        print(f"  ✅ Created valid state: target={state['target_file']}, iter={state['iteration']}")

    def test_state_can_be_updated(self):
        """State should be mutable (dict-based)."""
        state: SwarmState = {
            "target_file": "a.py",
            "test_file": "test_a.py",
            "code_content": "x = 1",
            "pylint_report": "",
            "test_report": "",
            "iteration": 0,
            "is_success": False,
            "task_description": None
        }
        # Simulate agent updates
        state["iteration"] = 1
        state["pylint_report"] = "score: 5.0/10"
        state["code_content"] = "x = 2  # fixed"
        state["is_success"] = True

        assert state["iteration"] == 1
        assert state["is_success"] is True
        assert "fixed" in state["code_content"]
        print(f"  ✅ State updated: iter={state['iteration']}, success={state['is_success']}")
