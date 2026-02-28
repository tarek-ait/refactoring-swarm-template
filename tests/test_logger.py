"""
=============================================================================
TEST 7: Logger Utility — Simulation
=============================================================================
Tests the experiment logger: writing, reading, validation, corruption
handling, and the ActionType enum.

Run:  python -m pytest tests/test_logger.py -v
=============================================================================
"""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import log_experiment, ActionType, LOG_FILE


@pytest.fixture(autouse=True)
def clean_log_file():
    """Ensure a clean log file for each test."""
    # Backup existing log
    backup = None
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            backup = f.read()

    # Start fresh
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "w") as f:
        f.write("[]")

    yield

    # Restore original log
    if backup is not None:
        with open(LOG_FILE, "w") as f:
            f.write(backup)


class TestActionTypeEnum:
    """Test the ActionType enum values."""

    def test_action_types_exist(self):
        assert ActionType.ANALYSIS.value == "CODE_ANALYSIS"
        assert ActionType.GENERATION.value == "CODE_GEN"
        assert ActionType.DEBUG.value == "DEBUG"
        assert ActionType.FIX.value == "FIX"
        print(f"  ✅ ActionTypes: {[a.value for a in ActionType]}")


class TestLogExperiment:
    """Test the core log_experiment function."""

    def test_basic_log_entry(self):
        log_experiment(
            agent_name="TestAgent",
            model_used="test-model",
            action=ActionType.ANALYSIS,
            details={"input_prompt": "analyze this", "output_response": "looks good"},
            status="SUCCESS"
        )
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
        assert len(data) == 1
        entry = data[0]
        assert entry["agent"] == "TestAgent"
        assert entry["model"] == "test-model"
        assert entry["action"] == "CODE_ANALYSIS"
        assert entry["status"] == "SUCCESS"
        assert "id" in entry
        assert "timestamp" in entry
        print(f"  ✅ Logged entry: agent={entry['agent']}, action={entry['action']}")

    def test_multiple_entries(self):
        for i in range(3):
            log_experiment(
                agent_name=f"Agent_{i}",
                model_used="model",
                action=ActionType.FIX,
                details={"input_prompt": f"fix {i}", "output_response": f"fixed {i}"},
                status="SUCCESS"
            )
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
        assert len(data) == 3
        print(f"  ✅ Logged 3 entries, got {len(data)} in file")

    def test_missing_required_fields_raises(self):
        """Missing input_prompt or output_response should raise ValueError."""
        with pytest.raises(ValueError, match="manquants"):
            log_experiment(
                agent_name="Bad",
                model_used="model",
                action=ActionType.FIX,
                details={"only_one_field": "incomplete"},  # Missing required keys
                status="FAILURE"
            )
        print("  ✅ Missing required fields correctly raises ValueError")

    def test_invalid_action_raises(self):
        """Invalid action type should raise ValueError."""
        with pytest.raises(ValueError, match="invalide"):
            log_experiment(
                agent_name="Bad",
                model_used="model",
                action="NONEXISTENT_ACTION",
                details={"input_prompt": "x", "output_response": "y"},
                status="FAILURE"
            )
        print("  ✅ Invalid action correctly raises ValueError")

    def test_string_action_accepted(self):
        """String values matching ActionType.value should be accepted."""
        log_experiment(
            agent_name="StringAction",
            model_used="model",
            action="FIX",  # String, not enum
            details={"input_prompt": "x", "output_response": "y"},
            status="SUCCESS"
        )
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
        assert data[-1]["action"] == "FIX"
        print("  ✅ String action 'FIX' accepted")


class TestCorruptedLogFile:
    """Test handling of corrupted log files."""

    def test_corrupted_json_recovers(self):
        """If the log file is corrupted, logger should recover."""
        with open(LOG_FILE, "w") as f:
            f.write("{{{invalid json")
        
        # This should NOT crash — it recovers
        log_experiment(
            agent_name="Recovery",
            model_used="model",
            action=ActionType.DEBUG,
            details={"input_prompt": "recover", "output_response": "ok"},
            status="SUCCESS"
        )
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
        assert len(data) == 1
        print("  ✅ Recovered from corrupted log file")
