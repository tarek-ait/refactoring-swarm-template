"""
=============================================================================
TEST 8: Custom Exceptions — Simulation
=============================================================================
Tests all custom exception types to make sure they carry context properly
and convert to dictionaries for logging.

Run:  python -m pytest tests/test_exceptions.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.exceptions import (
    ToolError,
    SecurityError,
    FileOpError,
    AnalysisError,
    TestError,
    ParsingError,
)


class TestToolError:
    """Test the base ToolError."""

    def test_message_and_context(self):
        err = ToolError("something broke", context={"key": "value"})
        assert err.message == "something broke"
        assert err.context == {"key": "value"}
        print(f"  ✅ ToolError: {err.message}, context={err.context}")

    def test_to_dict(self):
        err = ToolError("msg")
        d = err.to_dict()
        assert d["error_type"] == "ToolError"
        assert d["message"] == "msg"
        print(f"  ✅ to_dict: {d}")

    def test_default_context_is_empty(self):
        err = ToolError("no context")
        assert err.context == {}
        print("  ✅ Default context is empty dict")


class TestSecurityError:
    """Test SecurityError with attempted_path."""

    def test_with_path(self):
        err = SecurityError("traversal detected", attempted_path="../../etc/passwd")
        assert err.context["attempted_path"] == "../../etc/passwd"
        d = err.to_dict()
        assert d["error_type"] == "SecurityError"
        print(f"  ✅ SecurityError: path={err.context['attempted_path']}")

    def test_without_path(self):
        err = SecurityError("generic security issue")
        assert err.context == {}
        print("  ✅ SecurityError without path: context is empty")

    def test_is_tool_error(self):
        err = SecurityError("x")
        assert isinstance(err, ToolError)
        print("  ✅ SecurityError is a ToolError subclass")


class TestFileOpError:
    """Test FileOpError with filepath and original error."""

    def test_with_filepath_and_original(self):
        original = FileNotFoundError("nope")
        err = FileOpError("read failed", filepath="/sandbox/x.py", original_error=original)
        assert err.context["filepath"] == "/sandbox/x.py"
        assert err.context["error_type"] == "FileNotFoundError"
        print(f"  ✅ FileOpError: {err.context}")

    def test_without_extras(self):
        err = FileOpError("generic fail")
        assert "filepath" not in err.context
        print("  ✅ FileOpError without extras: clean context")


class TestAllExceptionsInheritToolError:
    """Verify the inheritance chain."""

    @pytest.mark.parametrize("exc_class", [
        SecurityError, FileOpError, AnalysisError, TestError, ParsingError
    ])
    def test_is_subclass(self, exc_class):
        assert issubclass(exc_class, ToolError)
        print(f"  ✅ {exc_class.__name__} is a ToolError subclass")

    def test_catch_all_with_tool_error(self):
        """All custom exceptions should be catchable via ToolError."""
        exceptions = [
            SecurityError("sec"),
            FileOpError("file"),
            AnalysisError("analysis"),
            TestError("test"),
            ParsingError("parse"),
        ]
        caught = 0
        for exc in exceptions:
            try:
                raise exc
            except ToolError:
                caught += 1
        assert caught == len(exceptions)
        print(f"  ✅ Caught all {caught} exceptions via ToolError base class")
