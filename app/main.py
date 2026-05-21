from fastapi import FastAPI, HTTPException

from app.models import RouteDecision, RouteRequest
from app.router import NoModelAvailable, choose_model


app = FastAPI(title="model-router")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/route", response_model=RouteDecision)
def route(request: RouteRequest) -> RouteDecision:
    try:
        model = choose_model(request)
    except NoModelAvailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    capability = request.capabilities[0] if request.capabilities else "default"

    return RouteDecision(
        model=model["name"],
        runner=model["runner"],
        route=model["endpoint"],
        output={
            "capability": capability,
            "reason": f"Selected model {model['name']} based on routing constraints",
            "input": request.input,
        },
    )
