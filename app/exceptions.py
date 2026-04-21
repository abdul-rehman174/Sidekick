class AIServiceException(Exception):
    """Base class for AI-related errors."""
    def __init__(self, message: str = "An internal AI error occurred."):
        self.message = message
        super().__init__(self.message)

class AIInferenceError(AIServiceException):
    """Raised when the API provider (Groq) fails or times out."""
    pass

class ToolExecutionError(AIServiceException):
    """Raised when a tool called by the AI fails to execute."""
    pass

class DataIntegrityError(Exception):
    """Raised when database operations fail safeguards."""
    pass
