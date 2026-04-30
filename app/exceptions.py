class AIServiceException(Exception):
    def __init__(self, message: str = "An internal AI error occurred."):
        self.message = message
        super().__init__(self.message)


class AIInferenceError(AIServiceException):
    pass


class ToolExecutionError(AIServiceException):
    pass
