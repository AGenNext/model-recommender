import json
import os
from pathlib import Path

from app.models import RouteRequest


REGISTRY_PATH = Path(
    os.getenv("MODEL_ROUTER_REGISTRY", "config/models.json")
)


class NoModelAvailable(Exception):
    pass


class InvalidModelRequested(Exception):
    pass


def load_registry() -> dict:
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_model(model: dict, request: RouteRequest) -> int:
    score = 0

    constraints = request.constraints

    score -= model.get("cost_rank", 100)
    score -= model.get("latency_rank", 100)
    score += model.get("quality_rank", 0)

    if constraints.provider and model.get("provider") == constraints.provider:
        score += 20

    if constraints.protocol and model.get("protocol") == constraints.protocol:
        score += 10

    for capability in request.capabilities:
        if capability in model.get("capabilities", []):
            score += 25

    return score


def choose_model(request: RouteRequest, requested_model: str | None = None) -> dict:
    registry = load_registry()

    if requested_model:
        for model in registry["models"]:
            if model["id"] == requested_model:
                return model

        raise InvalidModelRequested(requested_model)

    candidates = []

    for model in registry["models"]:
        if request.modality not in model.get("modalities", []):
            continue

        candidates.append((score_model(model, request), model))

    if not candidates:
        raise NoModelAvailable("No compatible model found")

    candidates.sort(key=lambda item: item[0], reverse=True)

    return candidates[0][1]
