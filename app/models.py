from dataclasses import dataclass, field
from typing import Any


@dataclass
class Constraints:
    latency: str | None = None
    cost: str | None = None
    quality: str | None = None
    provider: str | None = None
    runner: str | None = None
    protocol: str | None = None


@dataclass
class RouteRequest:
    task: str
    input: str
    capabilities: list[str] = field(default_factory=list)
    modality: str = "text"
    constraints: Constraints = field(default_factory=Constraints)


@dataclass
class RouteDecision:
    model: str
    provider: str
    runner: str
    route: str
    protocol: str
    output: dict[str, Any]
