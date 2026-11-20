"""Ports that outer parts implement. Application Core depends only on these protocols."""

from datetime import datetime
from typing import Protocol

from chromasense.core.models import EnhancementResult, SessionImage


class SessionImageStore(Protocol):
    """Keeps at most one original image and one enhancement result for each session."""

    def save_original(self, session_id: str, image: SessionImage) -> None:
        """Store the session's original image and discard any stored result."""

    def load_original(self, session_id: str) -> SessionImage | None:
        """Return the session's original image, or None if it has none."""

    def save_result(self, session_id: str, result: EnhancementResult) -> None:
        """Store the session's enhancement result, replacing any earlier one."""

    def load_result(self, session_id: str) -> EnhancementResult | None:
        """Return the session's enhancement result, or None if it has none."""

    def delete_session(self, session_id: str) -> None:
        """Delete everything stored for the session. Does nothing if it has nothing."""

    def idle_sessions(self, before: datetime) -> list[str]:
        """Return the IDs of sessions last used before the given time."""

    def touch(self, session_id: str, now: datetime) -> None:
        """Record that the session was used at the given time."""


class Clock(Protocol):
    """Gives the current time, so use cases can be tested with a fixed clock."""

    def now(self) -> datetime:
        """Return the current time."""
