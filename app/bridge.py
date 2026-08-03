"""Ponte autenticada que executa no computador somente ferramentas autorizadas."""

import os
from pathlib import Path
import secrets

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.tools.registry import ToolError, ToolRegistry

load_dotenv()

app = FastAPI(title="Hello Agent Local Bridge", version="1.0.0", docs_url=None, redoc_url=None)


class ToolRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    arguments: dict[str, object] = Field(default_factory=dict)


def get_registry() -> ToolRegistry:
    configured = os.getenv("ALLOWED_DIRECTORY", "").strip()
    if not configured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ALLOWED_DIRECTORY não configurado")
    directory = Path(configured).expanduser().resolve()
    if not directory.is_dir():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Pasta autorizada inválida")
    return ToolRegistry(directory)


def require_device_token(authorization: str | None = Header(default=None)) -> None:
    configured = os.getenv("BRIDGE_DEVICE_TOKEN", "").strip()
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not configured or not secrets.compare_digest(supplied, configured):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de dispositivo inválido")


@app.get("/health", dependencies=[Depends(require_device_token)])
def health(registry: ToolRegistry = Depends(get_registry)) -> dict[str, object]:
    return {"status": "ok", "tools": [item.name for item in registry.definitions]}


@app.post("/tools/execute", dependencies=[Depends(require_device_token)])
def execute_tool(payload: ToolRequest, registry: ToolRegistry = Depends(get_registry)) -> dict[str, object]:
    try:
        result = registry.execute(payload.name, payload.arguments)
    except ToolError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {"result": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.bridge:app", host="127.0.0.1", port=8787)
