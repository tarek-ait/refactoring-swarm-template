"""
Comprehensive unit tests for The Refactoring Swarm tools.

This test suite validates all tool functionality including:
- Sandbox security
- File operations
- Pylint integration
- Pytest integration  
- Code parsing

Run with: pytest tests/test_tools.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path

# Import all tools
from src.tools import (
    # Exceptions
    ToolError, SecurityError, FileOpError, AnalysisError, TestError, ParsingError,
    # Sandbox
    SandboxManager, initialize_sandbox, get_sandbox, get_safe_path,
    # File ops
    FileOperations, read_file, write_file, list_python_files,
    # Analysis
    PylintAnalyzer, run_pylint,
    # Testing
    PytestRunner, run_pytest,
    # Parsing
    CodeParser, extract_functions, extract_classes, get_imports
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_sandbox():
    """Create a temporary sandbox directory."""
    temp_dir = tempfile.mkdtemp(prefix="sandbox_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sandbox(temp_sandbox):
    """Create a SandboxManager instance."""
    return SandboxManager(temp_sandbox)


@pytest.fixture
def sample_python_file(temp_sandbox):
    """Create a sample Python file in the sandbox."""
    filepath = Path(temp_sandbox) / "sample.py"
    code = '''"""Sample module."""

def hello(name):
    """Greet someone."""
    return f"Hello, {name}!"

class Calculator:
    """Simple calculator."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
'''
    filepath.write_text(code)
    return filepath


@pytest.fixture
def bad_python_file(temp_sandbox):
    """Create a Python file with quality issues."""
    filepath = Path(temp_sandbox) / "bad_code.py"
    code = 'x=1\ny=2\nprint(x+y)'  # No spaces, no docstring
    filepath.write_text(code)
    return filepath


@pytest.fixture
def sample_test_file(temp_sandbox):
    """Create a sample test file."""
    test_dir = Path(temp_sandbox) / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_sample.py"
    code = '''def test_pass():
    assert 1 + 1 == 2

def test_fail():
    assert 1 + 1 == 3
'''
    test_file.write_text(code)
    return test_dir


# ============================================================================
# SANDBOX TESTS
# ============================================================================

class TestSandboxSecurity:
    """Test sandbox security features."""
    
    def test_sandbox_creation(self, temp_sandbox):
        """Test sandbox directory creation."""
        sandbox = SandboxManager(temp_sandbox)
        assert sandbox.sandbox_root.exists()
        assert sandbox.sandbox_root.is_dir()
    
    def test_path_traversal_blocked(self, sandbox):
        """Test that path traversal is blocked."""
        with pytest.raises(SecurityError):
            sandbox.validate_path("../../etc/passwd")
    