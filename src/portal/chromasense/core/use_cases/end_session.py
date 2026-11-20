"""Use case: delete everything stored for a session when it ends."""

from dataclasses import dataclass

from chromasense.core.ports import SessionImageStore


@dataclass(frozen=True)
class EndSessionRequest:
    """Which session to end."""

    session_id: str


class EndSession:
    """Delete everything stored for a session when the page closes.

    Args:
        store: The session image store.
    """

    def __init__(self, store: SessionImageStore) -> None:
        self._store = store

    def execute(self, request: EndSessionRequest) -> None:
        """Delete the session's original image and result.

        Args:
            request: The session to end. A session with nothing stored is not an error.
        """
        self._store.delete_session(request.session_id)
