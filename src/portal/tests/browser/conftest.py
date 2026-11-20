"""A live portal on a free port, with a temporary data folder, and a Playwright browser."""

import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from chromasense.main.settings import Settings
from chromasense.main.wiring import build_app

SAMPLES = Path(__file__).resolve().parents[3] / "color_engine" / "tests" / "data" / "samples"


class LiveServer:
    def __init__(self, url: str, data_dir: Path) -> None:
        self.url = url
        self.data_dir = data_dir

    def session_folders(self) -> list[str]:
        folder = self.data_dir / "sessions"
        return sorted(path.name for path in folder.iterdir()) if folder.exists() else []


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def server(tmp_path):
    port = _free_port()
    config = uvicorn.Config(
        build_app(Settings(data_dir=str(tmp_path))),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    instance = uvicorn.Server(config)
    thread = threading.Thread(target=instance.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not instance.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert instance.started, "portal did not start"
    yield LiveServer(url=f"http://127.0.0.1:{port}", data_dir=tmp_path)
    instance.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture
def page(browser, server):
    context = browser.new_context()
    page = context.new_page()
    page.goto(server.url)
    yield page
    context.close()


@pytest.fixture
def sample():
    return lambda name: str(SAMPLES / name)
