"""
=============================================================================
TEST 11: End-to-End Simulation (No LLM)
=============================================================================
Simulates the FULL pipeline locally without calling Mistral:
  1. Sets up a sandbox with buggy code + tests
  2. Runs auditor (pylint + pytest) to detect bugs
  3. Applies a manual fix (simulating the fixer)
  4. Runs judge (pytest) to verify the fix
  5. Checks state transitions

This proves the entire tool chain works end-to-end.

Run:  python -m pytest tests/test_e2e_simulation.py -v -s
=============================================================================
"""
import os
import sys
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.sandbox import SandboxManager, initialize_sandbox
from src.tools.file_ops import FileOperations
from src.tools.analyzer import PylintAnalyzer
from src.tools.tester import PytestRunner
from src.tools.parser import CodeParser


@pytest.fixture
def e2e_sandbox(tmp_path):
    """Create a full simulation sandbox."""
    sandbox_dir = tmp_path / "e2e_sandbox"
    sandbox_dir.mkdir()
    (sandbox_dir / "backup").mkdir()

    # --- Buggy code ---
    (sandbox_dir / "calculator.py").write_text('''"""A simple calculator."""

def add(a, b):
    """Add two numbers."""
    return a - b  # BUG: should be +

def is_even(n):
    """Check if number is even."""
    return n % 2 == 1  # BUG: should be == 0
''')

    # --- Tests that define correct behavior ---
    (sandbox_dir / "test_calculator.py").write_text('''"""Tests for calculator."""
from calculator import add, is_even

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 0) == 0

def test_is_even_true():
    assert is_even(4) is True

def test_is_even_false():
    assert is_even(3) is False

def test_is_even_zero():
    assert is_even(0) is True
''')

    # --- The correct (fixed) code ---
    fixed_code = '''"""A simple calculator."""

def add(a, b):
    """Add two numbers."""
    return a + b  # FIXED

def is_even(n):
    """Check if number is even."""
    return n % 2 == 0  # FIXED
'''

    sandbox = SandboxManager(str(sandbox_dir))
    return sandbox, sandbox_dir, fixed_code


class TestEndToEndSimulation:
    """Simulate the full Auditor → Fixer → Judge pipeline."""

    def test_step1_detect_bugs(self, e2e_sandbox):
        """STEP 1: Auditor detects that tests fail on buggy code."""
        sandbox, sandbox_dir, _ = e2e_sandbox
        runner = PytestRunner(sandbox, timeout=30)

        result = runner.run_tests("test_calculator.py")
        assert result.success is True
        assert result.all_tests_passed is False  # Bugs exist!
        assert result.stats.get("failed", 0) > 0
        print(f"\n  STEP 1 — Auditor detects bugs:")
        print(f"    Stats: {result.stats}")
        print(f"    Failed tests: {[ft.test_name for ft in result.failed_tests]}")
        print(f"  ✅ Bugs detected: {result.stats['failed']} failing tests")

    def test_step2_analyze_code(self, e2e_sandbox):
        """STEP 2: Auditor runs pylint on buggy code."""
        sandbox, _, _ = e2e_sandbox
        analyzer = PylintAnalyzer(sandbox, timeout=30)

        result = analyzer.analyze("calculator.py")
        assert result.success is True
        print(f"\n  STEP 2 — Pylint analysis:")
        print(f"    Score: {result.score}/10")
        print(f"    Issues: {len(result.issues)}")
        for issue in result.issues[:5]:
            print(f"    - Line {issue.line}: [{issue.type}] {issue.message}")
        print(f"  ✅ Analysis complete")

    def test_step3_parse_code(self, e2e_sandbox):
        """STEP 3: Parse the buggy code to understand structure."""
        sandbox, _, _ = e2e_sandbox
        parser = CodeParser(sandbox)

        functions = parser.extract_functions("calculator.py")
        names = [f.name for f in functions]
        print(f"\n  STEP 3 — Code parsing:")
        print(f"    Functions found: {names}")
        for f in functions:
            print(f"    - {f.name}({', '.join(f.parameters)}) at line {f.line_number}, docstring={f.has_docstring}")
        assert "add" in names
        assert "is_even" in names
        print(f"  ✅ Parsed {len(functions)} functions")

    def test_step4_apply_fix(self, e2e_sandbox):
        """STEP 4: Simulate the Fixer writing corrected code."""
        sandbox, sandbox_dir, fixed_code = e2e_sandbox
        file_ops = FileOperations(sandbox)

        # Backup original
        backup_result = file_ops.create_backup("calculator.py")
        assert backup_result.success is True
        print(f"\n  STEP 4 — Fixer applies fix:")
        print(f"    Backup created: {backup_result.metadata.get('backup_path', 'N/A')}")

        # Write fixed code
        write_result = file_ops.write_file("calculator.py", fixed_code, create_backup=False)
        assert write_result.success is True
        print(f"    Wrote fixed code to calculator.py")

        # Verify content
        read_result = file_ops.read_file("calculator.py")
        assert "a + b" in read_result.content
        assert "n % 2 == 0" in read_result.content
        print(f"  ✅ Fix applied successfully")

    def test_step5_judge_verifies(self, e2e_sandbox):
        """STEP 5: Judge runs tests on fixed code — all should pass."""
        sandbox, sandbox_dir, fixed_code = e2e_sandbox
        file_ops = FileOperations(sandbox)
        runner = PytestRunner(sandbox, timeout=30)

        # Apply the fix first
        file_ops.write_file("calculator.py", fixed_code, create_backup=False)

        # Judge runs tests
        result = runner.run_tests("test_calculator.py")
        assert result.success is True
        assert result.all_tests_passed is True
        assert result.stats.get("failed", 0) == 0
        rate = result.get_success_rate()
        print(f"\n  STEP 5 — Judge verification:")
        print(f"    Stats: {result.stats}")
        print(f"    Success rate: {rate}%")
        print(f"  ✅ ALL TESTS PASS — Bug fix verified!")

    def test_step6_full_pipeline(self, e2e_sandbox):
        """FULL PIPELINE: Run all steps in sequence, simulating the swarm."""
        sandbox, sandbox_dir, fixed_code = e2e_sandbox
        file_ops = FileOperations(sandbox)
        analyzer = PylintAnalyzer(sandbox, timeout=30)
        runner = PytestRunner(sandbox, timeout=30)
        parser = CodeParser(sandbox)

        print(f"\n{'='*60}")
        print(f"  FULL PIPELINE SIMULATION")
        print(f"{'='*60}")

        # ---- Iteration 1 ----
        print(f"\n  --- Iteration 1 ---")

        # Auditor: detect bugs
        test_result = runner.run_tests("test_calculator.py")
        pylint_result = analyzer.analyze("calculator.py")
        print(f"  Auditor: tests={'PASS' if test_result.all_tests_passed else 'FAIL'}, "
              f"pylint={pylint_result.score}/10")

        assert test_result.all_tests_passed is False  # Still buggy

        # Fixer: apply fix (simulated — normally this is the LLM)
        file_ops.write_file("calculator.py", fixed_code, create_backup=True)
        print(f"  Fixer: applied fix (simulated LLM output)")

        # Judge: verify
        judge_result = runner.run_tests("test_calculator.py")
        is_success = judge_result.all_tests_passed
        print(f"  Judge: tests={'PASS ✅' if is_success else 'FAIL ❌'}")

        assert is_success is True

        # State check
        final_state = {
            "target_file": str(sandbox_dir / "calculator.py"),
            "test_file": str(sandbox_dir / "test_calculator.py"),
            "iteration": 1,
            "is_success": is_success,
            "pylint_report": str(pylint_result.to_dict()),
            "test_report": str(judge_result.to_dict()),
        }
        print(f"\n  Final State:")
        print(f"    iteration: {final_state['iteration']}")
        print(f"    is_success: {final_state['is_success']}")
        print(f"\n  ✅ PIPELINE COMPLETE — Bugs fixed in 1 iteration!")
        print(f"{'='*60}")
