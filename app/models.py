from typing import Any
from pydantic import BaseModel, Field


class Constraints(BaseModel):
    latency: str | None = None
    cost: str | None = None
    quality: str | None = None


class RouteRequest(BaseModel):
    task: str
    input: str
    capabilities: list[str] = Field(default_factory=list)
    modality: str = "text"
    constraints: Constraints = Field(default_factory=Constraints)


class RouteDecision(BaseModel):
    model: str
    runner: str
    route: str
    output: dict[str, Any]
