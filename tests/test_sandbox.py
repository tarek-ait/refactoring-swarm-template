"""
=============================================================================
TEST 1: Sandbox Security Tool — Simulation
=============================================================================
Tests the SandboxManager to ensure path validation, traversal prevention,
and safe path resolution all work correctly.

Run:  python -m pytest tests/test_sandbox.py -v
=============================================================================
"""
import os
import sys
import tempfile
import shutil
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.sandbox import SandboxManager, initialize_sandbox, get_sandbox, get_safe_path
from src.tools.exceptions import SecurityError


@pytest.fixture
def tmp_sandbox(tmp_path):
    """Create a temporary sandbox directory for testing."""
    sandbox_dir = tmp_path / "test_sandbox"
    sandbox_dir.mkdir()
    # Create some test files inside
    (sandbox_dir / "good_file.py").write_text("print('hello')")
    (sandbox_dir / "subdir").mkdir()
    (sandbox_dir / "subdir" / "nested.py").write_text("x = 1")
    return SandboxManager(str(sandbox_dir))


class TestSandboxCreation:
    """Test sandbox initialization."""

    def test_sandbox_creates_directory(self, tmp_path):
        """Sandbox should create the directory if it doesn't exist."""
        new_dir = tmp_path / "brand_new_sandbox"
        assert not new_dir.exists()
        sandbox = SandboxManager(str(new_dir))
        assert new_dir.exists()
        print(f"  ✅ Created sandbox at: {sandbox.sandbox_root}")

    def test_sandbox_root_is_absolute(self, tmp_sandbox):
        """sandbox_root should always be an absolute path."""
        assert tmp_sandbox.sandbox_root.is_absolute()
        print(f"  ✅ Sandbox root is absolute: {tmp_sandbox.sandbox_root}")

    def test_empty_path_raises(self):
        """Empty sandbox path should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            SandboxManager("")
        print("  ✅ Empty path correctly rejected")


class TestPathValidation:
    """Test that validate_path blocks dangerous paths and allows safe ones."""

    def test_valid_relative_path(self, tmp_sandbox):
        """A relative path to an existing file should be validated."""
        result = tmp_sandbox.validate_path("good_file.py")
        assert result.exists()
        print(f"  ✅ Validated: good_file.py → {result}")

    def test_valid_nested_path(self, tmp_sandbox):
        """Nested relative paths should work."""
        result = tmp_sandbox.validate_path("subdir/nested.py")
        assert result.exists()
        print(f"  ✅ Validated nested: subdir/nested.py → {result}")

    def test_traversal_attack_blocked(self, tmp_sandbox):
        """Path traversal with ../ must be blocked."""
        with pytest.raises(SecurityError):
            tmp_sandbox.validate_path("../../etc/passwd")
        print("  ✅ Blocked path traversal: ../../etc/passwd")

    def test_absolute_path_outside_blocked(self, tmp_sandbox):
        """Absolute paths outside sandbox must be blocked."""
        with pytest.raises(SecurityError):
            tmp_sandbox.validate_path("/etc/passwd")
        print("  ✅ Blocked absolute path outside sandbox: /etc/passwd")

    def test_empty_path_raises(self, tmp_sandbox):
        """Empty path should raise ValueError."""
        with pytest.raises(ValueError):
            tmp_sandbox.validate_path("")
        print("  ✅ Empty path correctly rejected")


class TestIsSafe:
    """Test the non-throwing is_safe() method."""

    def test_safe_path_returns_true(self, tmp_sandbox):
        result = tmp_sandbox.is_safe("good_file.py")
        assert result is True
        print("  ✅ is_safe('good_file.py') = True")

    def test_dangerous_path_returns_false(self, tmp_sandbox):
        result = tmp_sandbox.is_safe("../../etc/shadow")
        assert result is False
        print("  ✅ is_safe('../../etc/shadow') = False")


class TestGetSafePath:
    """Test the convenience get_safe_path method."""

    def test_constructs_safe_path(self, tmp_sandbox):
        result = tmp_sandbox.get_safe_path("good_file.py")
        assert str(result).endswith("good_file.py")
        assert result.is_absolute()
        print(f"  ✅ get_safe_path → {result}")


class TestListPythonFiles:
    """Test listing Python files in sandbox."""

    def test_finds_all_python_files(self, tmp_sandbox):
        files = tmp_sandbox.list_python_files()
        names = [f.name for f in files]
        assert "good_file.py" in names
        assert "nested.py" in names
        print(f"  ✅ Found {len(files)} Python files: {names}")


class TestGlobalSandbox:
    """Test module-level initialize/get functions."""

    def test_initialize_and_get(self, tmp_path):
        sandbox_dir = tmp_path / "global_test"
        sandbox_dir.mkdir()
        sandbox = initialize_sandbox(str(sandbox_dir))
        retrieved = get_sandbox()
        assert sandbox.sandbox_root == retrieved.sandbox_root
        print(f"  ✅ Global sandbox init & retrieval works")
