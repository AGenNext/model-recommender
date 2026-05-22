from dataclasses import dataclass, field
from typing import Any


@dataclass
class Environment:
    side: str | None = None
    data_sensitivity: str | None = None


@dataclass
class Constraints:
    provider: str | None = None
    protocol: str | None = None
    side: str | None = None
    max_cost_usd: float | None = None
    min_context_tokens: int | None = None
    prefer_local: bool = False


@dataclass
class AgentContext:
    agent: str = "unknown"
    task: str = "general"
    input: str = ""
    modality: str = "text"
    capabilities: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    environment: Environment = field(default_factory=Environment)
    constraints: Constraints = field(default_factory=Constraints)


@dataclass
class Recommendation:
    model: str
    provider: str
    side: str
    route: str
    protocol: str
    estimated_cost_usd: float
    score: int
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
