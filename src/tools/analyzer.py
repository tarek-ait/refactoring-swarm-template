"""
Static code analysis module for The Refactoring Swarm.

This module provides integration with Pylint for code quality analysis.
It executes Pylint via subprocess and parses the results into structured format.

Features:
- Subprocess isolation (Pylint crashes don't affect main process)
- Timeout protection (30s default)
- JSON output parsing
- Quality score calculation
- Issue categorization by severity
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from .exceptions import AnalysisError, SecurityError
from .sandbox import SandboxManager


@dataclass
class Issue:
    """Represents a single Pylint issue.
    
    Attributes:
        type: Issue type (convention, refactor, warning, error, fatal)
        line: Line number where issue occurs
        column: Column number
        message: Human-readable description
        symbol: Pylint symbol (e.g., 'missing-docstring')
        message_id: Pylint message ID (e.g., 'C0111')
        severity: Numeric severity (0-10, higher = more severe)
    """
    type: str
    line: int
    column: int
    message: str
    symbol: str
    message_id: str = ""
    severity: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "symbol": self.symbol,
            "message_id": self.message_id,
            "severity": self.severity
        }


@dataclass
class AnalysisResult:
    """Result of Pylint analysis.
    
    Attributes:
        success: Whether analysis completed successfully
        score: Pylint quality score (0.0 - 10.0)
        issues: List of detected issues
        error: Error message if analysis failed
        metadata: Additional info (execution time, file analyzed, etc.)
    """
    success: bool
    score: float = 0.0
    issues: List[Issue] = field(default_factory=list)
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "score": self.score,
            "issues": [issue.to_dict() for issue in self.issues],
            "issue_count": len(self.issues),
            "error": self.error,
            "metadata": self.metadata
        }
    
    def is_improved(self, other: 'AnalysisResult') -> bool:
        """Check if this result is better than another.
        
        Args:
            other: Another AnalysisResult to compare against
            
        Returns:
            True if this result has a higher score
        """
        return self.score > other.score
    
    def get_issues_by_type(self) -> Dict[str, List[Issue]]:
        """Group issues by type.
        
        Returns:
            Dictionary mapping issue type to list of issues
        """
        grouped: Dict[str, List[Issue]] = {}
        for issue in self.issues:
            if issue.type not in grouped:
                grouped[issue.type] = []
            grouped[issue.type].append(issue)
        return grouped


class PylintAnalyzer:
    """Pylint integration for code quality analysis.
    
    This class executes Pylint via subprocess and parses the output
    into structured AnalysisResult objects.
    
    Example:
        >>> analyzer = PylintAnalyzer(sandbox, timeout=30)
        >>> result = analyzer.analyze("code.py")
        >>> print(f"Score: {result.score}/10")
        >>> for issue in result.issues:
        ...     print(f"Line {issue.line}: {issue.message}")
    """
    
    # Severity mapping for issue types
    SEVERITY_MAP = {
        "fatal": 10,
        "error": 8,
        "warning": 5,
        "refactor": 3,
        "convention": 1
    }
    
    def __init__(self, sandbox: SandboxManager, timeout: int = 30,
                 config_file: Optional[str] = None):
        """Initialize PylintAnalyzer.
        
        Args:
            sandbox: SandboxManager for path validation
            timeout: Maximum execution time in seconds (default: 30)
            config_file: Optional path to Pylint config file (.pylintrc)
        """
        self._sandbox = sandbox
        self._timeout = timeout
        self._config_file = config_file
    
    def analyze(self, filepath: Union[str, Path]) -> AnalysisResult:
        """Analyze a Python file with Pylint.
        
        This method:
        1. Validates the file path
        2. Constructs Pylint command
        3. Executes Pylint with timeout
        4. Parses JSON output
        5. Returns structured result
        
        Args:
            filepath: Path to Python file to analyze
            
        Returns:
            AnalysisResult with score and issues
            
        Example:
            >>> result = analyzer.analyze("messy_code.py")
            >>> if result.success:
            ...     print(f"Quality score: {result.score}/10")
        """
        start_time = datetime.now()
        
        try:
            # Validate path
            safe_path = self._sandbox.validate_path(filepath)
            
            # Check file exists
            if not safe_path.exists():
                return AnalysisResult(
                    success=False,
                    error=f"File not found: {safe_path}"
                )
            
            # Check it's a Python file
            if safe_path.suffix != '.py':
                return AnalysisResult(
                    success=False,
                    error=f"Not a Python file: {safe_path}"
                )
            
            # Run Pylint
            raw_output, return_code = self._run_pylint(safe_path)
            
            # Parse output
            score, issues = self._parse_output(raw_output)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Build metadata
            metadata = {
                "filepath": str(safe_path),
                "execution_time": execution_time,
                "return_code": return_code,
                "timestamp": datetime.now().isoformat(),
                "issue_count_by_type": self._count_by_type(issues)
            }
            
            return AnalysisResult(
                success=True,
                score=score,
                issues=issues,
                metadata=metadata
            )
            
        except subprocess.TimeoutExpired:
            return AnalysisResult(
                success=False,
                error=f"Pylint execution timeout after {self._timeout}s"
            )
        except SecurityError as e:
            return AnalysisResult(
                success=False,
                error=f"Security violation: {e.message}"
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=f"Analysis failed: {type(e).__name__}: {str(e)}"
            )
    
    def _run_pylint(self, filepath: Path) -> tuple[str, int]:
        """Execute Pylint as subprocess.
        
        Args:
            filepath: Validated path to Python file
            
        Returns:
            Tuple of (output string, return code)
            
        Raises:
            subprocess.TimeoutExpired: If execution exceeds timeout
        """
        # Build command
        cmd = [
            "pylint",
            "--output-format=json",  # Get machine-readable output
            "--score=yes",            # Include score in output
        ]
        
        # Add config file if specified
        if self._config_file:
            cmd.extend(["--rcfile", self._config_file])
        
        # Add file to analyze
        cmd.append(str(filepath))
        
        # Execute with timeout
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self._timeout,
            cwd=str(self._sandbox.sandbox_root)
        )
        
        return process.stdout, process.returncode
    
    def _parse_output(self, raw_output: str) -> tuple[float, List[Issue]]:
        """Parse Pylint JSON output.
        
        Args:
            raw_output: Raw Pylint output (JSON format)