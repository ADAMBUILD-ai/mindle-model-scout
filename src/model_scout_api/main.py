from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from src.model_scout.report import build_report
from src.model_scout.scout import HuggingFaceSearchError, scout as run_scout_core


ResourceType = Literal["model", "dataset", "space", "all"]


app = FastAPI(title="MINDLE MODEL SCOUT API", version=os.environ.get("MODEL_SCOUT_VERSION", "1.0.0"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _api_key_required() -> str | None:
    return (os.environ.get("MODEL_SCOUT_API_KEY") or "").strip() or None


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-KEY")):
    expected = _api_key_required()
    if expected is None:
        return
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing or invalid",
        )


class ScoutRequest(BaseModel):
    query: str = Field(min_length=1, description="Natural-language scout request text")
    limit: int = Field(default=10, ge=1, le=100, description="HF search result limit per source query")
    top_n: int = Field(default=5, ge=1, le=50, description="Number of top candidates returned in shortlist")
    resource: ResourceType = Field(default="model", description="model | dataset | space | all")


class ScoutResponse(BaseModel):
    service: str
    request: Dict[str, Any]
    response: Dict[str, Any]


@app.exception_handler(ValueError)
async def _value_error_handler(_request: Any, exc: ValueError):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.exception_handler(HuggingFaceSearchError)
async def _hf_error_handler(_request: Any, exc: HuggingFaceSearchError):
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"huggingface_upstream_error: {exc}")


@app.exception_handler(Exception)
async def _fallback_handler(_request: Any, exc: Exception):
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"unexpected_error: {exc}")


def _build_scout_payload(request: ScoutRequest) -> dict[str, Any]:
    raw = run_scout_core(request.query, request.limit, request.resource)
    report = build_report(raw, top_n=request.top_n)
    if not isinstance(report.get("comparison"), list):
        report["comparison"] = []
    report["checked_at"] = _utcnow_iso()
    return {
        "query": raw["query"],
        "search_query": raw["search_query"],
        "query_plan": raw["query_plan"],
        "resource_type": raw["resource_type"],
        "searched_candidate_count": raw["searched_candidate_count"],
        "candidate_count": raw.get("candidate_count", len(raw.get("candidates", []))),
        "top_n": request.top_n,
        "requested_at": _utcnow_iso(),
        "shortlist": report["shortlist"],
        "recommended": report["recommended"],
        "comparison": report["comparison"],
        "warnings": report["warnings"],
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "mindle-model-scout-api",
        "version": app.version,
        "checked_at": _utcnow_iso(),
    }


@app.get("/v1/capabilities")
def capabilities(_: None = Depends(require_api_key)):
    return {
        "service": "mindle-model-scout-api",
        "version": app.version,
        "resource_types": ["model", "dataset", "space", "all"],
        "limits": {"limit_min": 1, "limit_max": 100, "top_n_max": 50},
        "formats": {"response": "json", "input": {"query": "str", "limit": "int", "top_n": "int", "resource": "str"}},
        "auth": {"required": bool(_api_key_required()), "header": "X-API-KEY"},
        "endpoints": {
            "health": "/health",
            "capabilities": "/v1/capabilities",
            "scout": "/v1/scout",
        },
        "checked_at": _utcnow_iso(),
    }


@app.get("/v1/scout", response_model=ScoutResponse)
def get_scout(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    top_n: int = Query(5, ge=1, le=50),
    resource: ResourceType = Query("model"),
    _: None = Depends(require_api_key),
):
    req = ScoutRequest(query=query, limit=limit, top_n=top_n, resource=resource)
    payload = _build_scout_payload(req)
    return ScoutResponse(
        service="mindle-model-scout-api",
        request=req.model_dump(),
        response=payload,
    )


@app.post("/v1/scout", response_model=ScoutResponse)
def post_scout(payload: ScoutRequest, _: None = Depends(require_api_key)):
    response_payload = _build_scout_payload(payload)
    return ScoutResponse(service="mindle-model-scout-api", request=payload.model_dump(), response=response_payload)
