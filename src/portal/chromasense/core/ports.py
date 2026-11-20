"""Ports that outer parts implement. Application Core depends only on these protocols."""

from datetime import datetime
from typing import Protocol

from chromasense.core.models import SessionImage


class SessionImageStore(Protocol):
    def save_original(self, session_id: str, image: SessionImage) -> None:
        """Store the session's original image and discard any stored result."""

    def load_original(self, session_id: str) -> SessionImage | None: ...

    # EnhancementResult is added to chromasense.core.models in increment 12.
    def save_result(self, session_id: str, result: "EnhancementResult") -> None: ...  # noqa: F821

    def load_result(self, session_id: str) -> "EnhancementResult | None": ...  # noqa: F821

    def delete_session(self, session_id: str) -> None: ...

    def idle_sessions(self, before: datetime) -> list[str]: ...

    def touch(self, session_id: str, now: datetime) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
