import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from app.recommender import NoRecommendation, POLICY_PATH, REGISTRY_PATH, recommend


PORT = int(os.getenv("PORT", "8080"))
USAGE_PATH = Path(os.getenv("MODEL_RECOMMENDER_USAGE", "data/usage.jsonl"))


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json")
    handler.send_header("content-length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length", "0") or 0)
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def append_usage(event: dict[str, Any]) -> None:
    USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": int(time.time()), **event}
    with USAGE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "AGenNextModelRecommender/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(json.dumps({"ts": int(time.time()), "level": "info", "message": fmt % args}))

    def do_GET(self) -> None:
        if self.path == "/healthz":
            send_json(self, 200, {"status": "ok", "agent": "agennext-model-recommender"})
            return

        if self.path == "/readyz":
            ready = REGISTRY_PATH.exists() and POLICY_PATH.exists()
            send_json(self, 200 if ready else 503, {
                "status": "ready" if ready else "not_ready",
                "registry": str(REGISTRY_PATH),
                "policy": str(POLICY_PATH),
            })
            return

        send_json(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        try:
            payload = read_json(self)
        except json.JSONDecodeError:
            send_json(self, 400, {"error": "invalid_json"})
            return

        if self.path == "/recommend":
            try:
                result = recommend(payload)
                append_usage({"event": "recommend", "result": result})
                send_json(self, 200, result)
            except NoRecommendation as exc:
                send_json(self, 404, {"error": str(exc)})
            except FileNotFoundError as exc:
                send_json(self, 503, {"error": "missing_config", "detail": str(exc)})
            except Exception as exc:
                send_json(self, 500, {"error": "internal_error", "detail": str(exc)})
            return

        if self.path == "/usage":
            append_usage({"event": "usage", "payload": payload})
            send_json(self, 202, {"status": "accepted"})
            return

        send_json(self, 404, {"error": "not_found"})


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(json.dumps({"level": "info", "message": "starting", "port": PORT}))
    server.serve_forever()


if __name__ == "__main__":
    main()
