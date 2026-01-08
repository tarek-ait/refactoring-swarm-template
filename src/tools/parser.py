"""Code parsing using AST."""

from dataclasses import dataclass
from typing import List, Optional
import ast
from .sandbox import get_sandbox
from .exceptions import ParsingError


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    params: List[str]
    lineno: int


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    methods: List[str]
    lineno: int


class CodeParser:
    """Parse Python code with AST."""
    
    def __init__(self, sandbox_manager=None):
        self.sandbox = sandbox_manager or get_sandbox()
