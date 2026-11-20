"""Fakes for every Application Core port. Core tests use these instead of real adapters."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SAMPLES = Path(__file__).resolve().parents[3] / "color_engine" / "tests" / "data" / "samples"


class FakeSessionImageStore:
    def __init__(self) -> None:
        self.originals: dict = {}
        self.results: dict = {}
        self.touched: dict = {}
        self.calls: list[tuple] = []

    def save_original(self, session_id, image):
        self.calls.append(("save_original", session_id))
        self.originals[session_id] = image
        self.results.pop(session_id, None)

    def load_original(self, session_id):
        return self.originals.get(session_id)

    def save_result(self, session_id, result):
        self.calls.append(("save_result", session_id))
        self.results[session_id] = result

    def load_result(self, session_id):
        return self.results.get(session_id)

    def delete_session(self, session_id):
        self.calls.append(("delete_session", session_id))
        self.originals.pop(session_id, None)
        self.results.pop(session_id, None)
        self.touched.pop(session_id, None)

    def idle_sessions(self, before):
        return sorted(sid for sid, when in self.touched.items() if when < before)

    def touch(self, session_id, now):
        self.touched[session_id] = now


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)

    def now(self):
        return self.current

    def advance(self, minutes: float) -> None:
        self.current += timedelta(minutes=minutes)


@pytest.fixture
def store():
    return FakeSessionImageStore()


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def sample():
    def read(name: str) -> bytes:
        return (SAMPLES / name).read_bytes()

    return read
