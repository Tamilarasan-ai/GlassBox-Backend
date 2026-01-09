"""Custom Exception Classes"""


class BaseAppException(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AgentExecutionError(BaseAppException):
    """Raised when agent execution fails"""
    pass


class ToolExecutionError(BaseAppException):
    """Raised when a tool execution fails"""
    pass


class DatabaseError(BaseAppException):
    """Raised when database operations fail"""
    pass


class ValidationError(BaseAppException):
    """Raised when input validation fails"""
    pass


class ConfigurationError(BaseAppException):
    """Raised when configuration is invalid"""
    pass


class MaxIterationsExceeded(AgentExecutionError):
    """Raised when agent exceeds maximum iterations"""
    pass


class TimeoutError(AgentExecutionError):
    """Raised when agent execution times out"""
    pass
