"""Ponte autenticada: ferramentas fechadas e controle do runtime executivo local."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import secrets
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.mcf.adapter import MCFTaskRequest
from app.missions.models import MissionStatus
from app.runtime.factory import create_runtime
from app.tools.registry import ToolError, ToolRegistry

load_dotenv()

app = FastAPI(title="Hello Agent Local Bridge", version="3.0.0", docs_url=None, redoc_url=None)


class ToolRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    arguments: dict[str, object] = Field(default_factory=dict)


class MissionCreateRequest(BaseModel):
    mission_id: str = Field(min_length=1, max_length=128)
    requester_agent: str = Field(min_length=1, max_length=80)
    objective: str = Field(min_length=1, max_length=4000)
    return_to: str = Field(min_length=1, max_length=128)
    allowed_domains: list[str] = Field(default_factory=list, max_length=50)
    allowed_capabilities: list[str] = Field(default_factory=list, max_length=30)
    forbidden_actions: list[str] = Field(default_factory=list, max_length=50)
    completion_criteria: list[str] = Field(min_length=1, max_length=30)
    max_autonomy: int = Field(default=1, ge=1, le=5)
    owner_authorized: bool = False
    demo_only: bool = False


class StepCreateRequest(BaseModel):
    sequence: int = Field(ge=1, le=1000)
    action: str = Field(min_length=1, max_length=80)
    capability: str = Field(min_length=1, max_length=80)
    target: str = Field(default="", max_length=2048)
    parameters: dict[str, Any] = Field(default_factory=dict)


class MissionTransitionRequest(BaseModel):
    target: MissionStatus
    expected_version: int | None = Field(default=None, ge=1)


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    actor: str = Field(min_length=1, max_length=80)
    reason: str = Field(default="", max_length=500)


class EmergencyStopRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=500)


def get_registry() -> ToolRegistry:
    configured = os.getenv("ALLOWED_DIRECTORY", "").strip()
    if not configured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ALLOWED_DIRECTORY não configurado")
    directory = Path(configured).expanduser().resolve()
    if not directory.is_dir():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Pasta autorizada inválida")
    return ToolRegistry(directory)


@lru_cache
def get_mission_runtime():  # type: ignore[no-untyped-def]
    return create_runtime()


def _require_bearer(authorization: str | None, env_name: str, error_message: str) -> None:
    configured = os.getenv(env_name, "").strip()
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not configured or not secrets.compare_digest(supplied, configured):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, error_message)


def require_device_token(authorization: str | None = Header(default=None)) -> None:
    _require_bearer(authorization, "BRIDGE_DEVICE_TOKEN", "Token de dispositivo inválido")


def require_control_token(authorization: str | None = Header(default=None)) -> None:
    _require_bearer(authorization, "AEP_CONTROL_TOKEN", "Token de controle inválido")


@app.get("/health", dependencies=[Depends(require_device_token)])
def health(registry: ToolRegistry = Depends(get_registry)) -> dict[str, object]:
    service, _ = get_mission_runtime()
    active = service.repository.list_missions(
        (MissionStatus.READY, MissionStatus.RUNNING, MissionStatus.WAITING_HUMAN)
    )
    return {
        "status": "ok",
        "tools": [item.name for item in registry.definitions],
        "executive_runtime": True,
        "active_missions": len(active),
    }


@app.post("/tools/execute", dependencies=[Depends(require_device_token)])
def execute_tool(payload: ToolRequest, registry: ToolRegistry = Depends(get_registry)) -> dict[str, object]:
    try:
        result = registry.execute(payload.name, payload.arguments)
    except ToolError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {"result": result}


@app.post("/missions", dependencies=[Depends(require_control_token)], status_code=201)
def create_mission(payload: MissionCreateRequest) -> dict[str, object]:
    _, adapter = get_mission_runtime()
    try:
        mission = adapter.accept(MCFTaskRequest.from_payload(payload.model_dump()))
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {"mission_id": mission.mission_id, "status": mission.status.value, "version": mission.version}


@app.get("/missions/{mission_id}", dependencies=[Depends(require_control_token)])
def get_mission(mission_id: str) -> dict[str, object]:
    service, adapter = get_mission_runtime()
    try:
        mission = service.repository.get_mission(mission_id)
        packet = adapter.result_packet(mission_id)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Missão não encontrada") from exc
    return {
        "mission_id": mission.mission_id,
        "status": mission.status.value,
        "version": mission.version,
        "emergency_stopped": mission.emergency_stopped,
        "receipt": packet,
    }


@app.post("/missions/{mission_id}/transition", dependencies=[Depends(require_control_token)])
def transition_mission(mission_id: str, payload: MissionTransitionRequest) -> dict[str, object]:
    service, _ = get_mission_runtime()
    try:
        mission = service.transition(mission_id, payload.target, payload.expected_version)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {"mission_id": mission.mission_id, "status": mission.status.value, "version": mission.version}


@app.post("/missions/{mission_id}/steps", dependencies=[Depends(require_control_token)], status_code=201)
def create_step(mission_id: str, payload: StepCreateRequest) -> dict[str, object]:
    _, adapter = get_mission_runtime()
    try:
        step = adapter.add_step(
            mission_id,
            payload.sequence,
            payload.action,
            payload.capability,
            payload.target,
            payload.parameters,
        )
    except (KeyError, ValueError, RuntimeError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {
        "step_id": step.step_id,
        "status": step.status.value,
        "requires_approval": step.requires_approval,
        "risk": step.risk.value,
    }


@app.post("/missions/{mission_id}/steps/{step_id}/approval", dependencies=[Depends(require_control_token)])
def decide_approval(mission_id: str, step_id: str, payload: ApprovalDecisionRequest) -> dict[str, object]:
    service, _ = get_mission_runtime()
    try:
        step = service.repository.get_step(step_id)
        if step.mission_id != mission_id:
            raise ValueError("Etapa não pertence à missão")
        decision = service.decide_approval(step_id, payload.approved, payload.actor, payload.reason)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {"approval_id": decision.approval_id, "status": decision.status.value}


@app.post("/missions/{mission_id}/emergency-stop", dependencies=[Depends(require_control_token)])
def emergency_stop(mission_id: str, payload: EmergencyStopRequest) -> dict[str, object]:
    service, _ = get_mission_runtime()
    try:
        mission = service.emergency_stop(mission_id, payload.actor, payload.reason)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Missão não encontrada") from exc
    return {"mission_id": mission.mission_id, "status": mission.status.value, "emergency_stopped": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.bridge:app", host="127.0.0.1", port=8787)
