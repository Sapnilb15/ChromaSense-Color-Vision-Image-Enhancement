"""Errors that use cases raise, each with a message the user can read."""

from chromasense.core.models import UploadRejection


class UploadRejected(Exception):
    def __init__(self, reason: UploadRejection, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


class NoImageInSession(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
