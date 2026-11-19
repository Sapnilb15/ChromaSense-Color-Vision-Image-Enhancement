"""Shared Color Engine models: CVD profile and input limits."""

from dataclasses import dataclass
from enum import Enum


class CvdType(Enum):
    PROTAN = "protan"
    DEUTAN = "deutan"


@dataclass(frozen=True)
class CvdProfile:
    type: CvdType
    severity: float

    def __post_init__(self) -> None:
        if not isinstance(self.type, CvdType):
            raise ValueError("type must be a CvdType")
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")


@dataclass(frozen=True)
class InputLimits:
    max_bytes: int = 10 * 1024 * 1024
    max_megapixels: float = 12.0
