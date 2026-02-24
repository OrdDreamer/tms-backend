class ApplicationError(Exception):
    def __init__(self, message, extra=None):
        super().__init__(message)
        self.message = message
        self.extra = extra or {}


class ValidationError(ApplicationError):
    """
    Exception raised when a validation error occurs.
    """
    pass


class PermissionError(ApplicationError):
    """
    Exception raised when a user does not have permission to perform an action.
    """
    pass


class ProjectError(ApplicationError):
    """
    Exception raised when a project-related operation fails.
    """
    pass


class TranslationError(ApplicationError):
    """
    Exception raised when a translation-related operation fails.
    """
    pass
