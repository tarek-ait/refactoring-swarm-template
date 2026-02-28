"""
=============================================================================
TEST 4: Pytest Runner Tool — Simulation
=============================================================================
Tests the PytestRunner by executing real test files and verifying that
pass/fail stats, failed test details, and edge cases are handled.

Run:  python -m pytest tests/test_tester.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.sandbox import SandboxManager
from src.tools.tester import PytestRunner, TestResult, FailedTest


@pytest.fixture
def sandbox_with_tests(tmp_path):
    """Create a sandbox with passing and failing test files."""
    sandbox_dir = tmp_path / "tester_sandbox"
    sandbox_dir.mkdir()

    # A module that works correctly
    (sandbox_dir / "good_module.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef square(x):\n    return x * x\n"
    )

    # Tests that ALL PASS
    (sandbox_dir / "test_passing.py").write_text(
        "from good_module import add, square\n\n"
        "def test_add():\n    assert add(2, 3) == 5\n\n"
        "def test_square():\n    assert square(4) == 16\n\n"
        "def test_add_zero():\n    assert add(0, 0) == 0\n"
    )

    # A buggy module
    (sandbox_dir / "buggy_module.py").write_text(
        "def multiply(a, b):\n    return a + b  # BUG\n"
    )

    # Tests that FAIL
    (sandbox_dir / "test_failing.py").write_text(
        "from buggy_module import multiply\n\n"
        "def test_multiply_positive():\n    assert multiply(3, 4) == 12\n\n"
        "def test_multiply_zero():\n    assert multiply(0, 5) == 0\n"
    )

    # Empty test file
    (sandbox_dir / "test_empty.py").write_text("# No tests here\n")

    sandbox = SandboxManager(str(sandbox_dir))
    runner = PytestRunner(sandbox, timeout=30)
    return runner, sandbox_dir


class TestPassingTests:
    """Test running a test file where all tests pass."""

    def test_all_pass(self, sandbox_with_tests):
        runner, _ = sandbox_with_tests
        result = runner.run_tests("test_passing.py")
        assert result.success is True
        assert result.all_tests_passed is True
        assert result.stats.get("passed", 0) >= 3
        assert result.stats.get("failed", 0) == 0
        rate = result.get_success_rate()
        assert rate == 100.0
        print(f"  ✅ All tests passed: {result.stats} (success rate: {rate}%)")


class TestFailingTests:
    """Test running a test file where some tests fail."""

    def test_detects_failures(self, sandbox_with_tests):
        runner, _ = sandbox_with_tests
        result = runner.run_tests("test_failing.py")
        assert result.success is True  # Execution succeeded
        assert result.all_tests_passed is False  # But tests failed
        assert result.stats.get("failed", 0) >= 1
        print(f"  ✅ Detected failures: {result.stats}")
        for ft in result.failed_tests:
            print(f"     FAILED: {ft.test_name} — {ft.error_message}")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_nonexistent_test_file(self, sandbox_with_tests):
        runner, _ = sandbox_with_tests
        result = runner.run_tests("test_nonexistent.py")
        assert result.success is False
        print(f"  ✅ Missing file handled: {result.error}")

    def test_empty_test_file(self, sandbox_with_tests):
        runner, _ = sandbox_with_tests
        result = runner.run_tests("test_empty.py")
        # Should succeed but with 0 tests
        assert result.success is True
        assert result.stats.get("total", 0) == 0 or result.all_tests_passed is True
        print(f"  ✅ Empty test file: stats={result.stats}")


class TestTestResult:
    """Test the TestResult data class."""

    def test_success_rate_calculation(self):
        result = TestResult(
            success=True,
            stats={"total": 10, "passed": 7, "failed": 3, "skipped": 0, "errors": 0}
        )
        assert result.get_success_rate() == 70.0
        print(f"  ✅ Success rate: {result.get_success_rate()}%")

    def test_zero_total_success_rate(self):
        result = TestResult(success=True, stats={"total": 0})
        assert result.get_success_rate() == 0.0
        print("  ✅ Zero-total success rate = 0.0%")

    def test_to_dict(self):
        result = TestResult(
            success=True,
            all_tests_passed=False,
            stats={"total": 5, "passed": 3, "failed": 2},
            failed_tests=[
                FailedTest(test_name="test_x", test_file="t.py", error_message="assert 1 == 2")
            ]
        )
        d = result.to_dict()
        assert d["all_tests_passed"] is False
        assert len(d["failed_tests"]) == 1
        print(f"  ✅ to_dict: passed={d['stats']['passed']}, failed={d['stats']['failed']}")
