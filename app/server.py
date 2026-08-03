"""API web, PWA e webhook do WhatsApp."""

from functools import lru_cache
import json
import os
from pathlib import Path
import secrets
from typing import Annotated

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.chat_service import ChatService
from app.whatsapp import incoming_texts, send_text, valid_signature

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

app = FastAPI(title="Hello Agent", version="2.0.0")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str = Field(min_length=1, max_length=128)


class ChatResponse(BaseModel):
    reply: str


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
    )


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
    return {
        "status": "ok",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
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
    return ChatResponse(reply=reply)


@app.delete("/api/sessions/{session_id}", status_code=204, dependencies=[Depends(require_app_token)])
def reset_session(session_id: str, service: Annotated[ChatService, Depends(get_chat_service)]) -> None:
    service.reset(session_id)


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
