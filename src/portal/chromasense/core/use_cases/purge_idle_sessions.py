"""Use case: delete every session that has been idle longer than the configured time."""

from dataclasses import dataclass
from datetime import timedelta

from chromasense.core.ports import Clock, SessionImageStore


@dataclass(frozen=True)
class PurgeIdleSessionsRequest:
    pass


@dataclass(frozen=True)
class PurgeIdleSessionsResponse:
    deleted: int


class PurgeIdleSessions:
    def __init__(self, store: SessionImageStore, clock: Clock, idle_minutes: float) -> None:
        if idle_minutes <= 0:
            raise ValueError("idle_minutes must be positive")
        self._store = store
        self._clock = clock
        self._idle = timedelta(minutes=idle_minutes)

    def execute(self, request: PurgeIdleSessionsRequest) -> PurgeIdleSessionsResponse:
        idle = self._store.idle_sessions(self._clock.now() - self._idle)
        for session_id in idle:
            self._store.delete_session(session_id)
        return PurgeIdleSessionsResponse(deleted=len(idle))
