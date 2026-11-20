"""Request and response bodies for the HTTP API."""

from typing import Literal

from pydantic import BaseModel, Field


class EnhanceRequestBody(BaseModel):
    type: Literal["protan", "deutan"]
    severity: float = Field(ge=0.0, le=1.0)


class UploadResponseBody(BaseModel):
    width: int
    height: int


class PairBody(BaseModel):
    color_a_hex: str
    color_b_hex: str
    before: float
    after: float
    improved: bool


class EnhanceResponseBody(BaseModel):
    outcome: str
    message: str
    eligible_count: int
    improved_count: int
    pairs: list[PairBody]


class ErrorBody(BaseModel):
    reason: str
    message: str
