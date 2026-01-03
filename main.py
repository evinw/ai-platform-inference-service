from __future__ import annotations

import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI(title="Inference Service", version="1.0.0")

# --- Prometheus metrics (production-shaped) ---
REQUESTS = Counter(
    "inference_requests_total",
    "Total inference requests",
    ["endpoint", "status"],
)

LATENCY = Histogram(
    "inference_latency_seconds",
    "Inference latency in seconds",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

# --- Simple "model" mock ---
def mock_model_inference(inputs: List[float]) -> float:
    # Pretend we are calling an embedding model / classifier
    # This keeps the demo honest: infra patterns > ML complexity
    return float(sum(inputs) / max(len(inputs), 1))


# --- API schemas ---
class PredictRequest(BaseModel):
    request_id: str = Field(..., description="Client-provided request id for traceability")
    inputs: List[float] = Field(..., min_items=1, description="Numerical inputs")


class PredictResponse(BaseModel):
    request_id: str
    output: float
    model_version: str
    latency_ms: int


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    # Hook for checking downstream deps (db, model registry, etc.)
    return {"ready": True}


@app.get("/metrics")
def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    start = time.perf_counter()
    try:
        # Guardrails: keep API behavior predictable
        if any(not isinstance(x, (int, float)) for x in req.inputs):
            raise HTTPException(status_code=400, detail="inputs must be numeric")

        # Simulate small compute work
        out = mock_model_inference(req.inputs)

        latency_ms = int((time.perf_counter() - start) * 1000)
        REQUESTS.labels(endpoint="/predict", status="200").inc()
        LATENCY.labels(endpoint="/predict").observe((time.perf_counter() - start))

        return PredictResponse(
            request_id=req.request_id,
            output=out,
            model_version="mock-1.0.0",
            latency_ms=latency_ms,
        )
    except HTTPException:
        REQUESTS.labels(endpoint="/predict", status="400").inc()
        raise
    except Exception:
        REQUESTS.labels(endpoint="/predict", status="500").inc()
        raise HTTPException(status_code=500, detail="internal error")
