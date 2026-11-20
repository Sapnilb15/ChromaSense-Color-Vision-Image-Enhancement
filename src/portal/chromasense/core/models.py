"""Application Core models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np
from numpy.typing import NDArray

from color_engine.models import InputLimits


class UploadRejection(Enum):
    UNSUPPORTED_TYPE = "unsupported_type"
    CORRUPT = "corrupt"
    TOO_LARGE = "too_large"
    TOO_MANY_PIXELS = "too_many_pixels"


@dataclass(frozen=True)
class SessionImage:
    image_id: str
    pixels: NDArray[np.uint8]
    width: int
    height: int
    source_format: str
    uploaded_at: datetime


@dataclass(frozen=True)
class ProcessingSettings:
    threshold: float = 10.0
    color_count: int = 12
    input_limits: InputLimits = InputLimits()
