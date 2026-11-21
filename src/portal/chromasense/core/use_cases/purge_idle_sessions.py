"""Use case: delete every session that has been idle longer than the configured time."""

from dataclasses import dataclass
from datetime import timedelta

from chromasense.core.ports import Clock, SessionImageStore


@dataclass(frozen=True)
class PurgeIdleSessionsRequest:
    """No fields: the purge always uses the configured idle time."""

    pass


@dataclass(frozen=True)
class PurgeIdleSessionsResponse:
    """How many sessions were deleted."""

    deleted: int


class PurgeIdleSessions:
    """Delete every session that has been idle longer than the configured time.

    Args:
        store: The session image store.
        clock: The clock, used to find the idle cutoff.
        idle_minutes: How long a session may go unused. The default setting is 30.

    Raises:
        ValueError: If ``idle_minutes`` is not positive.
    """

    def __init__(self, store: SessionImageStore, clock: Clock, idle_minutes: float) -> None:
        if idle_minutes <= 0:
            raise ValueError("idle_minutes must be positive")
        self._store = store
        self._clock = clock
        self._idle = timedelta(minutes=idle_minutes)

    def execute(self, request: PurgeIdleSessionsRequest) -> PurgeIdleSessionsResponse:
        """Delete every session last used before now minus the idle time.

        Args:
            request: An empty request.

        Returns:
            The number of sessions deleted.
        """
        idle = self._store.idle_sessions(self._clock.now() - self._idle)
        for session_id in idle:
            self._store.delete_session(session_id)
        return PurgeIdleSessionsResponse(deleted=len(idle))
