"""
Code parsing utilities for The Refactoring Swarm.

This module provides Python AST (Abstract Syntax Tree) parsing functionality
to extract code structure information without executing the code.

Features:
- Extract function definitions
- Extract class definitions
- List imports
- Detect syntax errors
- Get code metrics
"""

import ast
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
from dataclasses import dataclass, field

from .exceptions import ParsingError, SecurityError
from .sandbox import SandboxManager
from .file_ops import read_file


@dataclass
class FunctionInfo:
    """Information about a function definition.
    
    Attributes:
        name: Function name
        line_number: Line where function is defined
        parameters: List of parameter names
        has_docstring: Whether function has a docstring
        is_async: Whether it's an async function
        decorators: List of decorator names
    """
    name: str
    line_number: int
    parameters: List[str] = field(default_factory=list)
    has_docstring: bool = False
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "line_number": self.line_number,
            "parameters": self.parameters,
            "has_docstring": self.has_docstring,
            "is_async": self.is_async,
            "decorators": self.decorators
        }


@dataclass
class ClassInfo:
    """Information about a class definition.
    
    Attributes:
        name: Class name
        line_number: Line where class is defined
        base_classes: List of base class names
        methods: List of method names
        has_docstring: Whether class has a docstring
    """
    name: str
    line_number: int
    base_classes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    has_docstring: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "line_number": self.line_number,
            "base_classes": self.base_classes,
            "methods": self.methods,
            "has_docstring": self.has_docstring
        }


@dataclass
class ImportInfo:
    """Information about an import statement.
    
    Attributes:
        module: Module name (e.g., 'os', 'sys')
        names: Imported names (e.g., ['path', 'join'] for 'from os import path, join')
        alias: Import alias (e.g., 'np' for 'import numpy as np')
        line_number: Line where import occurs
        is_from_import: Whether it's a 'from X import Y' statement
    """
    module: str
    line_number: int
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_from_import: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "module": self.module,
            "line_number": self.line_number,
            "names": self.names,
            "alias": self.alias,
            "is_from_import": self.is_from_import
        }


@dataclass
class CodeMetrics:
    """Code complexity metrics.
    
    Attributes:
        total_lines: Total line count
        code_lines: Non-empty, non-comment lines
        comment_lines: Comment line count
        function_count: Number of functions
        class_count: Number of classes
        import_count: Number of import statements
        max_line_length: Longest line length
    """
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    max_line_length: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "import_count": self.import_count,
            "max_line_length": self.max_line_length
        }


class CodeParser:
    """Python code parser using AST.
    
    This class parses Python code and extracts structural information
    without executing the code.
    
    Example:
        >>> parser = CodeParser(sandbox)
        >>> functions = parser.extract_functions("code.py")
        >>> for func in functions:
        ...     print(f"{func.name} at line {func.line_number}")
    """
    
    def __init__(self, sandbox: SandboxManager):
        """Initialize CodeParser.
        
        Args:
            sandbox: SandboxManager for path validation
        """
        self._sandbox = sandbox
    
    def parse_file(self, filepath: Union[str, Path]) -> Optional[ast.Module]:
        """Parse a Python file into an AST.
        
        Args:
            filepath: Path to Python file
            
        Returns:
            AST Module object, or None if parsing fails
            
        Raises:
            ParsingError: If file cannot be parsed
        """
        try:
            # Read file
            result = read_file(filepath, self._sandbox)
            if not result.success:
                raise ParsingError(
                    f"Failed to read file: {result.error}",
                    code_snippet=None
                )
            
            # Parse AST
            tree = ast.parse(result.content, filename=str(filepath))
            return tree
            
        except SyntaxError as e:
            raise ParsingError(
                f"Syntax error: {e.msg}",
                code_snippet=result.content[:200] if result.content else None,
                line_number=e.lineno
            )
        except Exception as e:
            raise ParsingError(
                f"Failed to parse: {str(e)}",
                code_snippet=None
            )
    
    def extract_functions(self, filepath: Union[str, Path]) -> List[FunctionInfo]:
        """Extract all function definitions from a file.
        
        Args:
            filepath: Path to Python file
            
        Returns:
            List of FunctionInfo objects
            
        Example:
            >>> functions = parser.extract_functions("code.py")
            >>> print(f"Found {len(functions)} functions")
        """
        try:
            tree = self.parse_file(filepath)