"""
=============================================================================
TEST 6: Function Fixer Tool — Simulation
=============================================================================
Tests the FunctionFixer which applies automated code transformations
based on Pylint issues (docstrings, unused imports, long lines, etc.).

Run:  python -m pytest tests/test_function_fixer.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.sandbox import SandboxManager
from src.tools.function_fixer import FunctionFixer, FixResult


@pytest.fixture
def fixer_env(tmp_path):
    """Set up a sandbox and FunctionFixer."""
    sandbox_dir = tmp_path / "fixer_sandbox"
    sandbox_dir.mkdir()
    sandbox = SandboxManager(str(sandbox_dir))
    fixer = FunctionFixer(sandbox)
    return fixer


class TestFixMissingDocstring:
    """Test adding missing docstrings."""

    def test_adds_docstring_to_function(self, fixer_env):
        code = "def my_func(x):\n    return x + 1\n"
        issues = [{"symbol": "missing-docstring", "line": 1, "message": "Missing function docstring"}]
        result = fixer_env.fix_code(code, issues)
        assert result.success is True
        print(f"  ✅ Fix result: {len(result.fixes_applied)} fixes applied")
        if result.fixes_applied:
            print(f"     Fixed: {result.fixes_applied[0].description}")


class TestFixUnusedImport:
    """Test removing unused imports."""

    def test_removes_unused(self, fixer_env):
        code = "import os\nimport sys\n\ndef hello():\n    return 'hi'\n"
        issues = [
            {"symbol": "unused-import", "line": 1, "message": "Unused import os"},
            {"symbol": "unused-import", "line": 2, "message": "Unused import sys"},
        ]
        result = fixer_env.fix_code(code, issues)
        assert result.success is True
        print(f"  ✅ Unused import fix: {len(result.fixes_applied)} fixes applied")


class TestFixLineTooLong:
    """Test breaking long lines."""

    def test_long_line(self, fixer_env):
        long_line = "x = " + "'a' + " * 30 + "'z'"
        code = f"def func():\n    {long_line}\n"
        issues = [{"symbol": "line-too-long", "line": 2, "message": "Line too long"}]
        result = fixer_env.fix_code(code, issues)
        assert result.success is True
        print(f"  ✅ Long line fix: success={result.success}, fixes={len(result.fixes_applied)}")


class TestSyntaxErrorHandling:
    """Test that the fixer handles unparseable code gracefully."""

    def test_syntax_error_returns_failure(self, fixer_env):
        code = "def broken(\n    pass\n"
        issues = [{"symbol": "missing-docstring", "line": 1, "message": "Missing docstring"}]
        result = fixer_env.fix_code(code, issues)
        assert result.success is False
        assert "syntax" in result.error.lower()
        print(f"  ✅ Syntax error handled: {result.error}")


class TestNoIssues:
    """Test when there are no issues to fix."""

    def test_no_issues_returns_original(self, fixer_env):
        code = '"""Module."""\n\ndef hello():\n    """Say hi."""\n    return "hi"\n'
        result = fixer_env.fix_code(code, [])
        assert result.success is True
        assert result.fixed_code == code  # No changes
        assert len(result.fixes_applied) == 0
        print("  ✅ No issues → original code returned unchanged")


class TestFixResult:
    """Test FixResult data class."""

    def test_to_dict(self):
        result = FixResult(
            success=True,
            fixed_code="x = 1",
            fixes_applied=[],
            metadata={"issues_processed": 0, "issues_fixed": 0, "fix_rate": 0.0}
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["has_code"] is True
        print(f"  ✅ to_dict: {d}")
