"""Storage Adapter: one folder per session under {root}/sessions/, deleted as a whole.

Layout of {root}/sessions/{session_id}/:
  original.npy, original.json   the decoded original and its metadata
  result.json, result.npz       the latest enhancement result (palette, labels, mask)
  enhanced.npy                  enhanced pixels, only for an ENHANCED outcome
  last_used                     an empty file whose modification time is the last use

Files are written under a temporary name and renamed, so a half-written file is never read.
Nothing here logs image content or paths.
"""

import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np

from chromasense.core.models import EnhancementResult, Outcome, PairOutcome, SessionImage
from color_engine.models import CvdProfile, CvdType, Palette2

_SESSION_ID = re.compile(r"[A-Za-z0-9_-]{16,128}")
_RESULT_FILES = ("result.json", "result.npz", "enhanced.npy")


class FilesystemSessionImageStore:
    """``SessionImageStore`` on the local filesystem, with one folder for each session.

    Every method raises ``ValueError`` if the session ID is not 16 to 128 URL-safe
    characters, so an ID can never name a path outside the sessions folder.

    Args:
        root: The data folder. Sessions are kept in ``root/sessions/``, created if missing.
    """

    def __init__(self, root: Path) -> None:
        self._sessions = Path(root) / "sessions"
        self._sessions.mkdir(parents=True, exist_ok=True)

    def save_original(self, session_id: str, image: SessionImage) -> None:
        """Store the original image, deleting the old result first."""
        folder = self._folder(session_id, create=True)
        # Remove the old result first, so it can never be paired with the new original.
        for name in _RESULT_FILES:
            (folder / name).unlink(missing_ok=True)
        _write_array(folder / "original.npy", image.pixels)
        _write_json(
            folder / "original.json",
            {
                "image_id": image.image_id,
                "width": image.width,
                "height": image.height,
                "source_format": image.source_format,
                "uploaded_at": image.uploaded_at.isoformat(),
            },
        )

    def load_original(self, session_id: str) -> SessionImage | None:
        """Return the stored original image, or None if there is none."""
        folder = self._folder(session_id)
        try:
            meta = json.loads((folder / "original.json").read_text(encoding="utf-8"))
            pixels = np.load(folder / "original.npy", allow_pickle=False)
        except FileNotFoundError:
            return None
        return SessionImage(
            image_id=meta["image_id"],
            pixels=pixels,
            width=meta["width"],
            height=meta["height"],
            source_format=meta["source_format"],
            uploaded_at=datetime.fromisoformat(meta["uploaded_at"]),
        )

    def save_result(self, session_id: str, result: EnhancementResult) -> None:
        """Store the enhancement result, writing ``result.json`` last."""
        folder = self._folder(session_id, create=True)
        if result.enhanced_pixels is None:
            (folder / "enhanced.npy").unlink(missing_ok=True)
        else:
            _write_array(folder / "enhanced.npy", result.enhanced_pixels)
        _write_npz(
            folder / "result.npz",
            colors_rgb=result.palette.colors_rgb,
            colors_lab=result.palette.colors_lab,
            labels=result.palette.labels,
            counts=result.palette.counts,
            mask=result.mask,
        )
        # result.json is written last; a result is only read when it exists.
        _write_json(
            folder / "result.json",
            {
                "image_id": result.image_id,
                "profile": {"type": result.profile.type.value, "severity": result.profile.severity},
                "outcome": result.outcome.value,
                "message": result.message,
                "has_enhanced": result.enhanced_pixels is not None,
                "pairs": [
                    {
                        "color_a_hex": pair.color_a_hex,
                        "color_b_hex": pair.color_b_hex,
                        "before": pair.before,
                        "after": pair.after,
                        "improved": pair.improved,
                    }
                    for pair in result.pairs
                ],
                "eligible_count": result.eligible_count,
                "improved_count": result.improved_count,
                "newly_confusable_count": result.newly_confusable_count,
            },
        )

    def load_result(self, session_id: str) -> EnhancementResult | None:
        """Return the stored enhancement result, or None if there is none."""
        folder = self._folder(session_id)
        try:
            meta = json.loads((folder / "result.json").read_text(encoding="utf-8"))
            with np.load(folder / "result.npz", allow_pickle=False) as arrays:
                palette = Palette2(
                    colors_rgb=arrays["colors_rgb"],
                    colors_lab=arrays["colors_lab"],
                    labels=arrays["labels"],
                    counts=arrays["counts"],
                )
                mask = arrays["mask"]
            enhanced = (
                np.load(folder / "enhanced.npy", allow_pickle=False)
                if meta["has_enhanced"]
                else None
            )
        except FileNotFoundError:
            return None
        return EnhancementResult(
            image_id=meta["image_id"],
            profile=CvdProfile(CvdType(meta["profile"]["type"]), meta["profile"]["severity"]),
            outcome=Outcome(meta["outcome"]),
            message=meta["message"],
            palette=palette,
            mask=mask,
            enhanced_pixels=enhanced,
            pairs=tuple(PairOutcome(**pair) for pair in meta["pairs"]),
            eligible_count=meta["eligible_count"],
            improved_count=meta["improved_count"],
            newly_confusable_count=meta["newly_confusable_count"],
        )

    def delete_session(self, session_id: str) -> None:
        """Delete the session's folder and everything in it."""
        shutil.rmtree(self._folder(session_id), ignore_errors=True)

    def idle_sessions(self, before: datetime) -> list[str]:
        """Return the IDs of session folders last used before the given time."""
        cutoff = before.timestamp()
        idle = []
        for folder in sorted(self._sessions.iterdir()):
            if not folder.is_dir() or not _SESSION_ID.fullmatch(folder.name):
                continue
            marker = folder / "last_used"
            last_used = (marker if marker.exists() else folder).stat().st_mtime
            if last_used < cutoff:
                idle.append(folder.name)
        return idle

    def touch(self, session_id: str, now: datetime) -> None:
        """Set the session's ``last_used`` time, creating its folder if needed."""
        marker = self._folder(session_id, create=True) / "last_used"
        marker.touch()
        os.utime(marker, (now.timestamp(), now.timestamp()))

    def _folder(self, session_id: str, create: bool = False) -> Path:
        if not isinstance(session_id, str) or not _SESSION_ID.fullmatch(session_id):
            raise ValueError("invalid session ID")
        folder = self._sessions / session_id
        if create:
            folder.mkdir(exist_ok=True)
        return folder


def _replace_atomically(path: Path, write) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            write(handle)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _write_array(path: Path, array) -> None:
    _replace_atomically(path, lambda handle: np.save(handle, np.asarray(array), allow_pickle=False))


def _write_npz(path: Path, **arrays) -> None:
    _replace_atomically(path, lambda handle: np.savez(handle, **arrays))


def _write_json(path: Path, data: dict) -> None:
    _replace_atomically(path, lambda handle: handle.write(json.dumps(data).encode("utf-8")))
