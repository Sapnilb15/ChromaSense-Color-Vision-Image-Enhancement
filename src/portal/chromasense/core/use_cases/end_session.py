"""Use case: delete everything stored for a session when it ends."""

from dataclasses import dataclass

from chromasense.core.ports import SessionImageStore


@dataclass(frozen=True)
class EndSessionRequest:
    session_id: str


class EndSession:
    def __init__(self, store: SessionImageStore) -> None:
        self._store = store

    def execute(self, request: EndSessionRequest) -> None:
        self._store.delete_session(request.session_id)
