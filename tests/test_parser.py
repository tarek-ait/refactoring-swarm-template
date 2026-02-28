"""
=============================================================================
TEST 5: Code Parser Tool — Simulation
=============================================================================
Tests the AST-based CodeParser: extracting functions, classes, imports,
and computing code metrics from real Python source.

Run:  python -m pytest tests/test_parser.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.sandbox import SandboxManager
from src.tools.parser import CodeParser, FunctionInfo, ClassInfo, ImportInfo, CodeMetrics
from src.tools.exceptions import ParsingError


@pytest.fixture
def sandbox_with_parseable(tmp_path):
    """Create a sandbox with various Python files for parsing."""
    sandbox_dir = tmp_path / "parser_sandbox"
    sandbox_dir.mkdir()

    # A rich module with functions, classes, imports
    (sandbox_dir / "rich_module.py").write_text('''"""A module with various constructs."""
import os
import sys
from pathlib import Path
from typing import List, Optional

def simple_function(x, y):
    """Add two numbers."""
    return x + y

def no_docstring(a):
    return a * 2

async def async_handler(request):
    """Handle a request asynchronously."""
    return {"status": "ok"}

class Animal:
    """Base animal class."""
    
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        """Make a sound."""
        return "..."

class Dog(Animal):
    """A dog."""
    
    def speak(self):
        return "Woof!"
    
    def fetch(self, item):
        return f"{self.name} fetches {item}"
''')

    # File with syntax error
    (sandbox_dir / "syntax_error.py").write_text("def broken(\n    pass\n")

    sandbox = SandboxManager(str(sandbox_dir))
    parser = CodeParser(sandbox)
    return parser, sandbox_dir


class TestExtractFunctions:
    """Test function extraction from AST."""

    def test_finds_all_functions(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        tree = parser.parse_file("rich_module.py")
        assert tree is not None

        # Use the module's extract logic
        functions = parser.extract_functions("rich_module.py")
        names = [f.name for f in functions]
        assert "simple_function" in names
        assert "no_docstring" in names
        assert "async_handler" in names
        print(f"  ✅ Found {len(functions)} functions: {names}")

    def test_detects_docstrings(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        functions = parser.extract_functions("rich_module.py")
        func_map = {f.name: f for f in functions}
        assert func_map["simple_function"].has_docstring is True
        assert func_map["no_docstring"].has_docstring is False
        print("  ✅ Docstring detection works")

    def test_detects_async(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        functions = parser.extract_functions("rich_module.py")
        func_map = {f.name: f for f in functions}
        assert func_map["async_handler"].is_async is True
        assert func_map["simple_function"].is_async is False
        print("  ✅ Async detection works")

    def test_extracts_parameters(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        functions = parser.extract_functions("rich_module.py")
        func_map = {f.name: f for f in functions}
        assert "x" in func_map["simple_function"].parameters
        assert "y" in func_map["simple_function"].parameters
        print(f"  ✅ Parameters: {func_map['simple_function'].parameters}")


class TestExtractClasses:
    """Test class extraction from AST."""

    def test_finds_all_classes(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        classes = parser.extract_classes("rich_module.py")
        names = [c.name for c in classes]
        assert "Animal" in names
        assert "Dog" in names
        print(f"  ✅ Found {len(classes)} classes: {names}")

    def test_detects_base_classes(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        classes = parser.extract_classes("rich_module.py")
        cls_map = {c.name: c for c in classes}
        assert "Animal" in cls_map["Dog"].base_classes
        print(f"  ✅ Dog inherits from: {cls_map['Dog'].base_classes}")

    def test_lists_methods(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        classes = parser.extract_classes("rich_module.py")
        cls_map = {c.name: c for c in classes}
        assert "speak" in cls_map["Animal"].methods
        assert "fetch" in cls_map["Dog"].methods
        print(f"  ✅ Dog methods: {cls_map['Dog'].methods}")


class TestExtractImports:
    """Test import extraction."""

    def test_finds_imports(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        imports = parser.extract_imports("rich_module.py")
        modules = [i.module for i in imports]
        assert "os" in modules
        assert "sys" in modules
        assert "pathlib" in modules
        print(f"  ✅ Found {len(imports)} imports: {modules}")


class TestSyntaxErrorHandling:
    """Test behavior with unparseable files."""

    def test_syntax_error_raises(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        with pytest.raises(ParsingError):
            parser.parse_file("syntax_error.py")
        print("  ✅ Syntax error correctly raises ParsingError")


class TestCodeMetrics:
    """Test code metrics calculation."""

    def test_metrics_computed(self, sandbox_with_parseable):
        parser, _ = sandbox_with_parseable
        metrics = parser.get_code_metrics("rich_module.py")
        assert metrics.total_lines > 0
        assert metrics.function_count >= 3
        assert metrics.class_count >= 2
        assert metrics.import_count >= 3
        print(f"  ✅ Metrics: {metrics.to_dict()}")
