"""Custom exceptions for tools."""


class ToolError(Exception):
    """Base exception for all tool errors."""
    
    def __init__(self, message, **context):
        super().__init__(message)
        self.message = message
        self.context = context
    
    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            **self.context
        }


class SecurityError(ToolError):
    """Raised when security validation fails."""
    pass
