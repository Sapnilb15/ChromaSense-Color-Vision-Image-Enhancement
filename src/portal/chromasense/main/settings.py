"""Configuration. This is the only module that reads the environment."""

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Server configuration, read from ``CHROMASENSE_*`` environment variables.

    Attributes:
        data_dir: Folder for session data (``CHROMASENSE_DATA_DIR``). Defaults to ``/data``.
        confusion_threshold: CIEDE2000 confusion threshold
            (``CHROMASENSE_CONFUSION_THRESHOLD``). Defaults to 10.
        palette_colors: Most palette colors (``CHROMASENSE_PALETTE_COLORS``). Defaults to 12.
        idle_minutes: Idle time before a session is deleted (``CHROMASENSE_IDLE_MINUTES``).
            Defaults to 30.
    """

    data_dir: str = "/data"
    confusion_threshold: float = 10.0
    palette_colors: int = 12
    idle_minutes: float = 30.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """Read settings from the environment, using the default for any unset or blank name.

        Args:
            env: Variables to read instead of ``os.environ``, for tests.

        Returns:
            The settings.

        Raises:
            ValueError: If a number cannot be parsed, or the threshold, palette colors, or
                idle minutes is not positive.
        """
        source = os.environ if env is None else env
        defaults = cls()

        def value(name: str, default: object) -> str:
            return source.get(f"CHROMASENSE_{name}", "").strip() or str(default)

        settings = cls(
            data_dir=value("DATA_DIR", defaults.data_dir),
            confusion_threshold=float(value("CONFUSION_THRESHOLD", defaults.confusion_threshold)),
            palette_colors=int(value("PALETTE_COLORS", defaults.palette_colors)),
            idle_minutes=float(value("IDLE_MINUTES", defaults.idle_minutes)),
        )
        if settings.confusion_threshold <= 0 or settings.palette_colors < 1:
            raise ValueError("CHROMASENSE_CONFUSION_THRESHOLD and PALETTE_COLORS must be positive")
        if settings.idle_minutes <= 0:
            raise ValueError("CHROMASENSE_IDLE_MINUTES must be positive")
        return settings
