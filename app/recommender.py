import json
import os
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(os.getenv("MODEL_RECOMMENDER_REGISTRY", "config/models.json"))
POLICY_PATH = Path(os.getenv("MODEL_RECOMMENDER_POLICY", "config/policy.json"))


class NoRecommendation(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def estimate_cost(model: dict[str, Any], context: dict[str, Any]) -> float:
    input_tokens = int(context.get("input_tokens") or 0)
    output_tokens = int(context.get("output_tokens") or 0)
    input_cost = float(model.get("input_cost_per_1m", 0))
    output_cost = float(model.get("output_cost_per_1m", 0))
    return round((input_tokens / 1_000_000 * input_cost) + (output_tokens / 1_000_000 * output_cost), 8)


def infer_capabilities(text: str) -> list[str]:
    text = (text or "").lower()
    capabilities: set[str] = set()

    keyword_map = {
        "code": ["code", "bug", "debug", "function", "api", "python", "javascript", "typescript"],
        "reasoning": ["reason", "think", "analyze", "compare", "decide", "plan"],
        "summarize": ["summarize", "summary", "tl;dr"],
        "chat": ["chat", "reply", "answer", "write"],
        "math": ["calculate", "math", "equation", "formula"],
    }

    for capability, words in keyword_map.items():
        if any(word in text for word in words):
            capabilities.add(capability)

    return sorted(capabilities)


def normalize_context(payload: dict[str, Any]) -> dict[str, Any]:
    context = dict(payload)
    text = " ".join(str(context.get(key, "")) for key in ("task", "input"))
    explicit = set(context.get("capabilities") or [])
    inferred = set(infer_capabilities(text))
    context["capabilities"] = sorted(explicit | inferred)
    context.setdefault("modality", "text")
    context.setdefault("constraints", {})
    context.setdefault("environment", {})
    context.setdefault("input_tokens", max(1, len(str(context.get("input", "")).split())))
    context.setdefault("output_tokens", 512)
    return context


def hard_reject(model: dict[str, Any], context: dict[str, Any], estimated_cost: float) -> str | None:
    constraints = context.get("constraints", {}) or {}
    environment = context.get("environment", {}) or {}

    if context.get("modality", "text") not in model.get("modalities", []):
        return "modality_mismatch"

    if constraints.get("provider") and model.get("provider") != constraints["provider"]:
        return "provider_mismatch"

    if constraints.get("protocol") and model.get("protocol") != constraints["protocol"]:
        return "protocol_mismatch"

    required_side = constraints.get("side") or environment.get("side")
    if required_side and model.get("side", model.get("provider")) != required_side:
        return "side_mismatch"

    min_context = constraints.get("min_context_tokens")
    if min_context and int(model.get("context_tokens", 0)) < int(min_context):
        return "insufficient_context"

    max_cost = constraints.get("max_cost_usd")
    if max_cost is not None and estimated_cost > float(max_cost):
        return "exceeds_max_cost"

    sensitivity = environment.get("data_sensitivity")
    if sensitivity in {"private", "secret", "restricted"}:
        if model.get("side", model.get("provider")) != "local":
            return "private_data_requires_local"

    return None


def score_model(model: dict[str, Any], context: dict[str, Any], policy: dict[str, Any], estimated_cost: float) -> tuple[int, list[str]]:
    weights = policy.get("weights", {})
    penalties = policy.get("penalties", {})
    constraints = context.get("constraints", {}) or {}
    reasons: list[str] = []
    score = 0

    required_caps = set(context.get("capabilities") or [])
    model_caps = set(model.get("capabilities") or [])
    matched_caps = required_caps & model_caps

    if required_caps:
        score += len(matched_caps) * int(weights.get("capability_match", 40))
        missing = required_caps - model_caps
        if missing:
            score -= int(penalties.get("missing_required_capability", 1000)) * len(missing)
        else:
            reasons.append("matched_required_capabilities")

    if constraints.get("prefer_local") and model.get("side", model.get("provider")) == "local":
        score += int(weights.get("local_preference", 10))
        reasons.append("local_preference")

    if constraints.get("provider") and model.get("provider") == constraints["provider"]:
        score += int(weights.get("provider_match", 5))

    if constraints.get("protocol") and model.get("protocol") == constraints["protocol"]:
        score += int(weights.get("protocol_match", 5))

    score += int(float(model.get("success_rate", policy.get("modes", {}).get(policy.get("environment_mode", "test"), {}).get("default_success_rate", 0.5))) * int(weights.get("observed_success_rate", 30)))
    score += int(float(model.get("quality_score", policy.get("modes", {}).get(policy.get("environment_mode", "test"), {}).get("default_quality_score", 0.5))) * int(weights.get("quality_score", 20)))
    score += int(float(model.get("efficiency_score", policy.get("modes", {}).get(policy.get("environment_mode", "test"), {}).get("default_efficiency_score", 0.5))) * int(weights.get("efficiency_score", 20)))

    score -= int(model.get("cost_rank", 1)) * int(penalties.get("cost_rank", 3))
    score -= int(model.get("latency_rank", 1)) * int(penalties.get("latency_rank", 2))
    score -= int(estimated_cost * 1_000_000)

    return score, reasons


def recommend(payload: dict[str, Any]) -> dict[str, Any]:
    context = normalize_context(payload)
    registry = load_json(REGISTRY_PATH)
    policy = load_json(POLICY_PATH)

    candidates: list[tuple[int, float, int, str, dict[str, Any], list[str]]] = []

    for model in registry.get("models", []):
        cost = estimate_cost(model, context)
        rejection = hard_reject(model, context, cost)
        if rejection:
            continue

        score, reasons = score_model(model, context, policy, cost)
        candidates.append((score, cost, int(model.get("latency_rank", 999)), str(model.get("id", model.get("name"))), model, reasons))

    if not candidates:
        raise NoRecommendation("no_model_satisfies_context")

    candidates.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
    score, cost, _, model_id, model, reasons = candidates[0]

    return {
        "advisor": "agennext-model-recommender",
        "recommendation": {
            "model": model_id,
            "provider": model.get("provider"),
            "side": model.get("side", model.get("provider")),
            "route": model.get("endpoint"),
            "protocol": model.get("protocol"),
        },
        "estimated_cost_usd": cost,
        "score": score,
        "reason": ",".join(reasons) if reasons else "highest_deterministic_score",
        "policy_version": policy.get("policy_version"),
        "registry_version": registry.get("registry_version"),
        "decision_mode": policy.get("decision_mode", "single_best_model"),
        "metadata": {
            "capabilities": context.get("capabilities", []),
            "input_tokens": context.get("input_tokens"),
            "output_tokens": context.get("output_tokens"),
        },
    }
