"""Test execution using Pytest."""

from dataclasses import dataclass
from typing import List, Optional
import subprocess
from .sandbox import get_sandbox
from .exceptions import TestError


@dataclass
class FailedTest:
    """Information about a failed test."""
    test_name: str
    test_file: str
    error_message: str


@dataclass
class TestResult:
    """Result of test execution."""
    success: bool
    all_tests_passed: bool = False
    stats: Optional[dict] = None
    failed_tests: List[FailedTest] = None
    error: Optional[str] = None


class PytestRunner:
    """Run tests with Pytest."""
    
    def __init__(self, sandbox_manager=None):
        self.sandbox = sandbox_manager or get_sandbox()
