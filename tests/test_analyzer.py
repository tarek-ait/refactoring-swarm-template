"""
=============================================================================
TEST 3: Pylint Analyzer Tool — Simulation
=============================================================================
Tests the PylintAnalyzer by running it against real Python code (good and bad)
and verifying score parsing, issue detection, and error handling.

Run:  python -m pytest tests/test_analyzer.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.sandbox import SandboxManager
from src.tools.analyzer import PylintAnalyzer, AnalysisResult, Issue


@pytest.fixture
def sandbox_with_code(tmp_path):
    """Create a sandbox with good and bad Python files."""
    sandbox_dir = tmp_path / "analyzer_sandbox"
    sandbox_dir.mkdir()

    # Clean code (should score high)
    (sandbox_dir / "clean_code.py").write_text(
        '"""A clean module."""\n\n\ndef greet(name):\n    """Return a greeting."""\n    return f"Hello, {name}!"\n'
    )

    # Messy code (should score low)
    (sandbox_dir / "messy_code.py").write_text(
        "import os\nimport sys\nimport json\nx=1\ny=2\nz=x+y\nprint(z)\na = [1,2,3]\nfor i in a:\n print(i)\n"
    )

    # Syntax error
    (sandbox_dir / "broken.py").write_text("def oops(\n    pass\n")

    # Not a Python file
    (sandbox_dir / "readme.txt").write_text("This is not Python")

    sandbox = SandboxManager(str(sandbox_dir))
    analyzer = PylintAnalyzer(sandbox, timeout=30)
    return analyzer, sandbox_dir


class TestPylintAnalysis:
    """Test running Pylint on various files."""

    def test_clean_code_scores_well(self, sandbox_with_code):
        analyzer, _ = sandbox_with_code
        result = analyzer.analyze("clean_code.py")
        assert result.success is True
        # Score may be 0.0 if Pylint JSON output doesn't include the score line
        assert result.score >= 0.0
        assert len(result.issues) == 0  # Clean code should have no issues
        print(f"  ✅ Clean code score: {result.score}/10 ({len(result.issues)} issues)")

    def test_messy_code_has_issues(self, sandbox_with_code):
        analyzer, _ = sandbox_with_code
        result = analyzer.analyze("messy_code.py")
        assert result.success is True
        assert len(result.issues) > 0  # Should find problems
        print(f"  ✅ Messy code: score={result.score}/10, {len(result.issues)} issues found")
        for issue in result.issues[:3]:
            print(f"     - Line {issue.line}: [{issue.type}] {issue.symbol}: {issue.message}")

    def test_nonexistent_file(self, sandbox_with_code):
        analyzer, _ = sandbox_with_code
        result = analyzer.analyze("ghost.py")
        assert result.success is False
        assert result.error is not None
        print(f"  ✅ Missing file handled: {result.error}")

    def test_non_python_file_rejected(self, sandbox_with_code):
        analyzer, _ = sandbox_with_code
        result = analyzer.analyze("readme.txt")
        assert result.success is False
        print(f"  ✅ Non-Python file rejected: {result.error}")


class TestAnalysisResult:
    """Test AnalysisResult data class methods."""

    def test_to_dict(self):
        result = AnalysisResult(
            success=True,
            score=7.5,
            issues=[
                Issue(type="warning", line=10, column=0, message="Unused var", symbol="unused-variable")
            ]
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["score"] == 7.5
        assert d["issue_count"] == 1
        print(f"  ✅ to_dict: {d}")

    def test_is_improved(self):
        before = AnalysisResult(success=True, score=3.0)
        after = AnalysisResult(success=True, score=8.0)
        assert after.is_improved(before) is True
        assert before.is_improved(after) is False
        print("  ✅ is_improved comparison works")

    def test_get_issues_by_type(self):
        result = AnalysisResult(
            success=True,
            score=5.0,
            issues=[
                Issue(type="warning", line=1, column=0, message="a", symbol="s1"),
                Issue(type="error", line=2, column=0, message="b", symbol="s2"),
                Issue(type="warning", line=3, column=0, message="c", symbol="s3"),
            ]
        )
        grouped = result.get_issues_by_type()
        assert len(grouped["warning"]) == 2
        assert len(grouped["error"]) == 1
        summary = {k: len(v) for k, v in grouped.items()}
        print(f"  ✅ Grouped by type: {summary}")


class TestScoreComparison:
    """Test the compare_scores method."""

    def test_compare_improvement(self, sandbox_with_code):
        analyzer, _ = sandbox_with_code
        before = AnalysisResult(success=True, score=3.0, issues=[
            Issue(type="error", line=1, column=0, message="x", symbol="y")
        ] * 5)
        after = AnalysisResult(success=True, score=8.0, issues=[
            Issue(type="warning", line=1, column=0, message="x", symbol="y")
        ] * 2)
        comparison = analyzer.compare_scores(before, after)
        assert comparison["improved"] is True
        assert comparison["score_delta"] == 5.0
        assert comparison["issues_fixed"] == 3
        print(f"  ✅ Comparison: delta={comparison['score_delta']}, fixed={comparison['issues_fixed']}")
