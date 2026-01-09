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