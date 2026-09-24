"""Small real model-serving fixture used by the local progressive delivery demo."""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response

REQUESTS = Counter(
    "model_runtime_requests_total", "Predictions served by the local fixture", ["model", "version"]
)
LATENCY = Histogram(
    "model_runtime_prediction_duration_seconds",
    "Prediction duration for the local fixture",
    ["model", "version"],
)


class PredictionRequest(BaseModel):
    features: list[float] = Field(min_length=2, max_length=2)


def create_app() -> FastAPI:
    model_path = Path(os.environ["MODEL_PATH"])
    model_name = os.environ.get("MODEL_NAME", "risk-classifier")
    model_version = os.environ.get("MODEL_VERSION", "local")
    delay_ms = int(os.environ.get("MODEL_DELAY_MS", "0"))
    state: dict[str, object] = {}

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        state["model"] = joblib.load(model_path)
        yield
        state.clear()

    app = FastAPI(title=f"Local model runtime: {model_name}:{model_version}", lifespan=lifespan)

    @app.get("/healthz")
    def health() -> dict[str, object]:
        return {
            "status": "ok" if "model" in state else "starting",
            "model": model_name,
            "version": model_version,
            "delay_ms": delay_ms,
        }

    @app.post("/v1/predict")
    def predict(request: PredictionRequest) -> dict[str, object]:
        model = state.get("model")
        if model is None:
            raise HTTPException(status_code=503, detail="model is not loaded")
        with LATENCY.labels(model_name, model_version).time():
            started = time.perf_counter()
            if delay_ms:
                time.sleep(delay_ms / 1000)
            prediction = int(model.predict([request.features])[0])
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        REQUESTS.labels(model_name, model_version).inc()
        return {
            "prediction": prediction,
            "model": model_name,
            "version": model_version,
            "latency_ms": elapsed_ms,
        }

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
