"""API web, PWA, webhook do WhatsApp e relay controlado de missões MCF."""

from __future__ import annotations

from functools import lru_cache
import json
import logging
import os
from pathlib import Path
import secrets
from typing import Annotated, Any

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.chat_service import ChatService
from app.mcf.remote import RemoteMissionClient, RemoteMissionError
from app.tools.base import ToolExecutor
from app.tools.registry import ToolRegistry
from app.tools.remote import EmptyToolRegistry, RemoteToolRegistry
from app.whatsapp import incoming_texts, send_text, valid_signature

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
logger = logging.getLogger(__name__)

app = FastAPI(title="Hello Agent", version="3.0.0")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str = Field(min_length=1, max_length=128)


class ChatResponse(BaseModel):
    reply: str


class MissionRelayRequest(BaseModel):
    mission_id: str = Field(min_length=1, max_length=128)
    requester_agent: str = Field(min_length=1, max_length=80)
    objective: str = Field(min_length=1, max_length=4000)
    return_to: str = Field(min_length=1, max_length=128)
    allowed_domains: list[str] = Field(default_factory=list, max_length=50)
    allowed_capabilities: list[str] = Field(default_factory=list, max_length=30)
    forbidden_actions: list[str] = Field(default_factory=list, max_length=50)
    completion_criteria: list[str] = Field(min_length=1, max_length=30)
    max_autonomy: int = Field(default=1, ge=1, le=5)


class MissionTransitionRelayRequest(BaseModel):
    target: str = Field(min_length=1, max_length=40)
    expected_version: int | None = Field(default=None, ge=1)


class MissionStepRelayRequest(BaseModel):
    sequence: int = Field(ge=1, le=1000)
    action: str = Field(min_length=1, max_length=80)
    capability: str = Field(min_length=1, max_length=80)
    target: str = Field(default="", max_length=2048)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ApprovalRelayRequest(BaseModel):
    approved: bool
    actor: str = Field(min_length=1, max_length=80)
    reason: str = Field(default="", max_length=500)


class EmergencyRelayRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=500)


def get_tool_registry(allowed: Path) -> ToolExecutor:
    bridge_url = os.getenv("BRIDGE_URL", "").strip()
    bridge_token = os.getenv("BRIDGE_DEVICE_TOKEN", "").strip()
    if bridge_url and bridge_token:
        return RemoteToolRegistry(bridge_url, bridge_token)
    if os.getenv("VERCEL"):
        return EmptyToolRegistry()
    return ToolRegistry(allowed)


@lru_cache
def get_chat_service() -> ChatService:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    allowed = Path(os.getenv("ALLOWED_DIRECTORY", str(ROOT))).expanduser().resolve()
    if not allowed.is_dir():
        allowed = ROOT
    return ChatService(
        key,
        os.getenv("MODEL_NAME", "gemini-3.6-flash"),
        allowed,
        os.getenv("FALLBACK_MODEL_NAME", "gemini-3.5-flash-lite"),
        registry=get_tool_registry(allowed),
    )


@lru_cache
def get_mission_client() -> RemoteMissionClient:
    bridge_url = os.getenv("BRIDGE_URL", "").strip()
    control_token = os.getenv("AEP_CONTROL_TOKEN", "").strip()
    if not bridge_url or not control_token:
        raise RuntimeError("Runtime executivo não configurado")
    return RemoteMissionClient(bridge_url, control_token)


def require_app_token(authorization: str | None = Header(default=None)) -> None:
    configured = os.getenv("APP_ACCESS_TOKEN", "").strip()
    if not configured:
        if os.getenv("VERCEL"):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "APP_ACCESS_TOKEN não configurado")
        return
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not secrets.compare_digest(supplied, configured):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de acesso inválido")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(PUBLIC / "index.html")


@app.get("/{asset_name}", include_in_schema=False)
def pwa_asset(asset_name: str) -> FileResponse:
    allowed_assets = {"app.js", "styles.css", "sw.js", "manifest.webmanifest", "icon.svg"}
    if asset_name not in allowed_assets:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado")
    return FileResponse(PUBLIC / asset_name)


@app.get("/api/health")
def health() -> dict[str, object]:
    bridge_url = os.getenv("BRIDGE_URL", "").strip()
    bridge_token = os.getenv("BRIDGE_DEVICE_TOKEN", "").strip()
    bridge_connected = False
    if bridge_url and bridge_token:
        try:
            bridge_connected = RemoteToolRegistry(bridge_url, bridge_token).health()
        except ValueError:
            pass
    return {
        "status": "ok",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "bridge_configured": bool(bridge_url and bridge_token),
        "bridge_connected": bridge_connected,
        "executive_configured": bool(bridge_url and os.getenv("AEP_CONTROL_TOKEN")),
        "whatsapp_configured": all(
            os.getenv(name)
            for name in ("WHATSAPP_VERIFY_TOKEN", "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_APP_SECRET")
        ),
    }


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(require_app_token)])
def chat(payload: ChatRequest, service: Annotated[ChatService, Depends(get_chat_service)]) -> ChatResponse:
    try:
        reply = service.chat(payload.session_id, payload.message)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except Exception as exc:
        logger.exception("Falha ao processar conversa na sessão %s", payload.session_id)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "O serviço de IA não conseguiu responder. Tente novamente.") from exc
    return ChatResponse(reply=reply)


@app.delete("/api/sessions/{session_id}", status_code=204, dependencies=[Depends(require_app_token)])
def reset_session(session_id: str, service: Annotated[ChatService, Depends(get_chat_service)]) -> None:
    service.reset(session_id)


def _relay_error(exc: Exception) -> HTTPException:
    if isinstance(exc, RuntimeError) and not isinstance(exc, RemoteMissionError):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    return HTTPException(status.HTTP_502_BAD_GATEWAY, "Runtime executivo indisponível")


@app.post("/api/missions", dependencies=[Depends(require_app_token)], status_code=201)
def relay_create_mission(payload: MissionRelayRequest) -> dict[str, Any]:
    try:
        return get_mission_client().create_mission(payload.model_dump())
    except (RuntimeError, RemoteMissionError, ValueError) as exc:
        raise _relay_error(exc) from exc


@app.get("/api/missions/{mission_id}", dependencies=[Depends(require_app_token)])
def relay_get_mission(mission_id: str) -> dict[str, Any]:
    try:
        return get_mission_client().get_mission(mission_id)
    except (RuntimeError, RemoteMissionError, ValueError) as exc:
        raise _relay_error(exc) from exc


@app.post("/api/missions/{mission_id}/transition", dependencies=[Depends(require_app_token)])
def relay_transition_mission(mission_id: str, payload: MissionTransitionRelayRequest) -> dict[str, Any]:
    try:
        return get_mission_client().transition(mission_id, payload.target, payload.expected_version)
    except (RuntimeError, RemoteMissionError, ValueError) as exc:
        raise _relay_error(exc) from exc


@app.post("/api/missions/{mission_id}/steps", dependencies=[Depends(require_app_token)], status_code=201)
def relay_add_step(mission_id: str, payload: MissionStepRelayRequest) -> dict[str, Any]:
    try:
        return get_mission_client().add_step(mission_id, payload.model_dump())
    except (RuntimeError, RemoteMissionError, ValueError) as exc:
        raise _relay_error(exc) from exc


@app.post("/api/missions/{mission_id}/steps/{step_id}/approval", dependencies=[Depends(require_app_token)])
def relay_approval(mission_id: str, step_id: str, payload: ApprovalRelayRequest) -> dict[str, Any]:
    try:
        return get_mission_client().approve(mission_id, step_id, payload.approved, payload.actor, payload.reason)
    except (RuntimeError, RemoteMissionError, ValueError) as exc:
        raise _relay_error(exc) from exc


@app.post("/api/missions/{mission_id}/emergency-stop", dependencies=[Depends(require_app_token)])
def relay_emergency_stop(mission_id: str, payload: EmergencyRelayRequest) -> dict[str, Any]:
    try:
        return get_mission_client().emergency_stop(mission_id, payload.actor, payload.reason)
    except (RuntimeError, RemoteMissionError, ValueError) as exc:
        raise _relay_error(exc) from exc


@app.get("/api/whatsapp/webhook", response_class=PlainTextResponse)
def verify_whatsapp(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
) -> str:
    configured = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if mode != "subscribe" or not configured or not secrets.compare_digest(token, configured):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Falha na verificação do webhook")
    return challenge


def answer_whatsapp(sender: str, message: str) -> None:
    reply = get_chat_service().chat(f"whatsapp:{sender}", message)
    send_text(
        sender,
        reply,
        os.environ["WHATSAPP_ACCESS_TOKEN"],
        os.environ["WHATSAPP_PHONE_NUMBER_ID"],
        os.getenv("WHATSAPP_GRAPH_VERSION", "v23.0"),
    )


@app.post("/api/whatsapp/webhook", status_code=200)
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    body = await request.body()
    if not valid_signature(body, x_hub_signature_256, os.getenv("WHATSAPP_APP_SECRET", "")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Assinatura inválida")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JSON inválido") from exc
    for sender, message in incoming_texts(payload):
        background_tasks.add_task(answer_whatsapp, sender, message)
    return {"status": "accepted"}
