"""Errors that use cases raise, each with a message the user can read."""

from chromasense.core.models import UploadRejection


class UploadRejected(Exception):
    """Raised when an uploaded file cannot be used as the session's image.

    Args:
        reason: Why the file was rejected.
        message: The reason in words the user can read.
    """

    def __init__(self, reason: UploadRejection, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


class NoImageInSession(Exception):
    """Raised when a use case needs an image or result that the session does not have.

    Args:
        message: What the user needs to do, in words the user can read.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
