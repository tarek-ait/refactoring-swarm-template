"""Sandbox security for file operations."""

from pathlib import Path
from .exceptions import SecurityError


class SandboxManager:
    """Manages sandbox security for file operations."""
    
    def __init__(self, sandbox_path):
        self.sandbox_root = Path(sandbox_path).resolve()
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
