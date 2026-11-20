"""Request and response bodies for the HTTP API."""

from typing import Literal

from pydantic import BaseModel, Field


class EnhanceRequestBody(BaseModel):
    """Body of ``POST /api/image/enhance``: the profile type and a severity from 0 to 1."""

    type: Literal["protan", "deutan"]
    severity: float = Field(ge=0.0, le=1.0)


class UploadResponseBody(BaseModel):
    """Body returned by ``POST /api/image``: the image size in pixels."""

    width: int
    height: int


class PairBody(BaseModel):
    """One flagged color pair and its simulated separation before and after."""

    color_a_hex: str
    color_b_hex: str
    before: float
    after: float
    improved: bool


class EnhanceResponseBody(BaseModel):
    """Body returned by ``POST /api/image/enhance``: the outcome, its message, and the pairs."""

    outcome: str
    message: str
    eligible_count: int
    improved_count: int
    pairs: list[PairBody]


class ErrorBody(BaseModel):
    """Body of every error response: a reason code and a message the user can read."""

    reason: str
    message: str
