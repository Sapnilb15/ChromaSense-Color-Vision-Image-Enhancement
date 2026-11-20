"""Composition root: construct every part and wire them together."""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool

import chromasense
from chromasense.core.models import ProcessingSettings
from chromasense.core.use_cases.end_session import EndSession
from chromasense.core.use_cases.enhance_image import EnhanceImage
from chromasense.core.use_cases.export_image import ExportImage
from chromasense.core.use_cases.process_upload import ProcessUpload
from chromasense.core.use_cases.purge_idle_sessions import (
    PurgeIdleSessions,
    PurgeIdleSessionsRequest,
)
from chromasense.core.use_cases.render_view import RenderView
from chromasense.main.settings import Settings
from chromasense.storage.filesystem_session_image_store import FilesystemSessionImageStore
from chromasense.web_api.app import UseCases, create_app

PURGE_INTERVAL_SECONDS = 60
TEMPLATES_DIR = Path(chromasense.__file__).parent / "web_ui" / "templates"


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def build_app(
    settings: Settings, purge_interval_seconds: float = PURGE_INTERVAL_SECONDS
) -> FastAPI:
    clock = SystemClock()
    store = FilesystemSessionImageStore(Path(settings.data_dir))
    processing = ProcessingSettings(
        threshold=settings.confusion_threshold, color_count=settings.palette_colors
    )
    purge = PurgeIdleSessions(store, clock, idle_minutes=settings.idle_minutes)
    use_cases = UseCases(
        process_upload=ProcessUpload(store, clock, processing),
        enhance_image=EnhanceImage(store, clock, processing),
        render_view=RenderView(store, clock),
        export_image=ExportImage(store, clock),
        end_session=EndSession(store),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # A server restart ends every session (Decision 3), so delete what is left.
        for session_id in store.idle_sessions(clock.now() + timedelta(days=36500)):
            store.delete_session(session_id)
        task = asyncio.create_task(_purge_forever(purge, purge_interval_seconds))
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    return create_app(
        use_cases,
        max_upload_bytes=processing.input_limits.max_bytes,
        templates_dir=TEMPLATES_DIR,
        lifespan=lifespan,
    )


_log = logging.getLogger(__name__)


async def _purge_forever(purge: PurgeIdleSessions, interval_seconds: float) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await run_in_threadpool(purge.execute, PurgeIdleSessionsRequest())
        except Exception as error:  # keep purging; never log paths or image data
            _log.warning("idle session purge failed: %s", type(error).__name__)
