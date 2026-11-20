import pytest

from chromasense.core.use_cases.end_session import EndSession, EndSessionRequest
from chromasense.core.use_cases.purge_idle_sessions import (
    PurgeIdleSessions,
    PurgeIdleSessionsRequest,
)

FIRST = "first-session-000000"
SECOND = "second-session-00000"


def test_end_session_deletes_the_session(store):
    store.originals[FIRST] = "image"
    EndSession(store).execute(EndSessionRequest(session_id=FIRST))
    assert ("delete_session", FIRST) in store.calls
    assert FIRST not in store.originals


def test_purge_deletes_only_sessions_idle_longer_than_the_limit(store, clock):
    store.touch(FIRST, clock.now())
    clock.advance(25)
    store.touch(SECOND, clock.now())
    clock.advance(6)  # FIRST idle 31 minutes, SECOND idle 6 minutes

    response = PurgeIdleSessions(store, clock, idle_minutes=30).execute(PurgeIdleSessionsRequest())

    assert response.deleted == 1
    assert ("delete_session", FIRST) in store.calls
    assert ("delete_session", SECOND) not in store.calls


def test_purge_with_nothing_idle_deletes_nothing(store, clock):
    store.touch(FIRST, clock.now())
    response = PurgeIdleSessions(store, clock, idle_minutes=30).execute(PurgeIdleSessionsRequest())
    assert response.deleted == 0
    assert store.calls == []


def test_idle_minutes_must_be_positive(store, clock):
    with pytest.raises(ValueError):
        PurgeIdleSessions(store, clock, idle_minutes=0)
