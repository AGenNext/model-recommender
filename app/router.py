import json
from pathlib import Path

from app.models import RouteRequest


REGISTRY_PATH = Path("config/models.json")


class NoModelAvailable(Exception):
    pass


def load_registry() -> dict:
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


PRIORITY = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "basic": 1,
    "good": 2,
    "best": 3,
}


def score_model(model: dict, request: RouteRequest) -> int:
    score = 0

    constraints = request.constraints

    if constraints.cost and model.get("cost") == constraints.cost:
        score += 3

    if constraints.latency and model.get("latency") == constraints.latency:
        score += 3

    if constraints.quality and model.get("quality") == constraints.quality:
        score += 3

    for capability in request.capabilities:
        if capability in model.get("capabilities", []):
            score += 5

    return score


def choose_model(request: RouteRequest) -> dict:
    registry = load_registry()
    candidates = []

    for model in registry["models"]:
        if request.modality not in model.get("modalities", []):
            continue

        candidates.append((score_model(model, request), model))

    if not candidates:
        raise NoModelAvailable("No compatible model found")

    candidates.sort(key=lambda item: item[0], reverse=True)

    return candidates[0][1]
