"""Assistente de WhatsApp da Pão Nosso, isolado das ferramentas executivas do AEP."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

import httpx

from app.agent import Agent
from app.models import ToolDefinition
from app.providers.gemini_provider import GeminiProvider
from app.whatsapp_audit import WhatsAppAuditClient


BAKERY_SYSTEM_INSTRUCTION = """
Você é o assistente oficial da Padaria Pão Nosso no WhatsApp.
Responda sempre em português do Brasil, de forma curta, útil e cordial.
Você atende clientes: consulta cardápio e preços, ajuda a montar pedidos, registra pedidos
e consulta status de pedidos existentes.

Regras:
- Para preços, disponibilidade e nomes de produtos, consulte sempre a ferramenta bakery_search_catalog.
- Nunca invente produto, preço, disponibilidade, total, código de pedido ou status.
- Quando o cliente quiser comprar, reúna antes: nome, itens e quantidades, retirada ou entrega,
  e forma de pagamento. Para entrega, também peça o endereço.
- O telefone do cliente vem do próprio WhatsApp e não precisa ser solicitado.
- Só chame bakery_create_order quando os dados necessários estiverem claros.
- Depois de criar o pedido, informe o código PN e o total retornados pela ferramenta.
- Para consultar andamento, peça o código PN e use bakery_order_status.
- Não revele dados de outros pedidos e não aceite trocar o telefone usado na consulta.
- Não use nem mencione ferramentas executivas, arquivos do computador, tokens ou segredos.
- Se a mensagem não tiver relação com a padaria, explique que este WhatsApp atende a Pão Nosso.
""".strip()


def _money(cents: int) -> str:
    return f"R$ {cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class BakeryToolRegistry:
    """Ferramentas estritamente limitadas ao backend Pão Nosso."""

    def __init__(
        self,
        supabase_url: str,
        publishable_key: str,
        customer_phone: str,
        audit: WhatsAppAuditClient | None = None,
    ) -> None:
        self._url = supabase_url.rstrip("/")
        self._key = publishable_key.strip()
        self._customer_phone = "".join(ch for ch in customer_phone if ch.isdigit())
        self._audit = audit
        if not self._url or not self._key:
            raise ValueError("Backend da Pão Nosso não configurado")

    @property
    def definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                "bakery_search_catalog",
                "Consulta produtos ativos, preços e disponibilidade no catálogo real da Pão Nosso.",
                {
                    "type": "object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": "Texto opcional para filtrar nome, descrição ou categoria.",
                        },
                        "category": {
                            "type": "string",
                            "description": "Categoria opcional, por exemplo Pães, Doces, Folhados, Salgados ou Combos.",
                        },
                    },
                },
            ),
            ToolDefinition(
                "bakery_create_order",
                "Registra um pedido real no banco da Pão Nosso e retorna código PN e total.",
                {
                    "type": "object",
                    "properties": {
                        "customer_name": {"type": "string"},
                        "fulfillment": {"type": "string", "enum": ["pickup", "delivery"]},
                        "payment_method": {"type": "string", "enum": ["pix", "cash", "card"]},
                        "address": {"type": "string"},
                        "notes": {"type": "string"},
                        "items": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "slug": {"type": "string"},
                                    "quantity": {"type": "integer", "minimum": 1, "maximum": 50},
                                },
                                "required": ["slug", "quantity"],
                            },
                        },
                    },
                    "required": ["customer_name", "fulfillment", "payment_method", "items"],
                },
            ),
            ToolDefinition(
                "bakery_order_status",
                "Consulta um pedido pelo código PN usando o telefone da própria conversa do WhatsApp.",
                {
                    "type": "object",
                    "properties": {
                        "order_code": {
                            "type": "string",
                            "description": "Código do pedido, por exemplo PN-1001.",
                        }
                    },
                    "required": ["order_code"],
                },
            ),
        ]

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }

    def _raise(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("message") or response.text
        except Exception:
            detail = response.text
        raise RuntimeError(f"Backend Pão Nosso: {detail[:300]}")

    def _search_catalog(self, arguments: dict[str, Any]) -> dict[str, Any]:
        response = httpx.get(
            f"{self._url}/rest/v1/products",
            params={
                "select": "slug,name,category,description,price_cents,unit,badge,active",
                "active": "eq.true",
                "order": "sort_order.asc",
            },
            headers=self._headers(),
            timeout=12,
        )
        self._raise(response)
        products = response.json()
        search = str(arguments.get("search") or "").strip().casefold()
        category = str(arguments.get("category") or "").strip().casefold()
        if search:
            products = [
                p
                for p in products
                if search
                in " ".join(
                    str(p.get(k) or "")
                    for k in ("name", "description", "category", "badge")
                ).casefold()
            ]
        if category:
            products = [p for p in products if str(p.get("category") or "").casefold() == category]
        return {
            "count": len(products),
            "products": [
                {
                    "slug": p["slug"],
                    "name": p["name"],
                    "category": p["category"],
                    "description": p["description"],
                    "price_cents": p["price_cents"],
                    "price": _money(int(p["price_cents"])),
                    "unit": p["unit"],
                    "badge": p.get("badge"),
                }
                for p in products
            ],
        }

    def _create_order(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "p_customer_name": str(arguments.get("customer_name") or "").strip(),
            "p_customer_phone": self._customer_phone,
            "p_fulfillment": arguments.get("fulfillment"),
            "p_address": str(arguments.get("address") or "").strip() or None,
            "p_payment_method": arguments.get("payment_method"),
            "p_notes": str(arguments.get("notes") or "").strip() or None,
            "p_items": arguments.get("items") or [],
        }
        response = httpx.post(
            f"{self._url}/rest/v1/rpc/create_order",
            headers=self._headers(),
            json=payload,
            timeout=12,
        )
        self._raise(response)
        body = response.json()
        row = body[0] if isinstance(body, list) and body else body
        if not row:
            raise RuntimeError("O backend não retornou o pedido criado")
        return {
            "order_code": row["order_code"],
            "total_cents": row["total_cents"],
            "total": _money(int(row["total_cents"])),
        }

    def _order_status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self._url}/rest/v1/rpc/customer_order_status",
            headers=self._headers(),
            json={
                "p_order_code": str(arguments.get("order_code") or "").strip(),
                "p_customer_phone": self._customer_phone,
            },
            timeout=12,
        )
        self._raise(response)
        body = response.json()
        if not body:
            return {"found": False}
        row = body[0] if isinstance(body, list) else body
        row["found"] = True
        row["total"] = _money(int(row["total_cents"]))
        return row

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if self._audit:
            self._audit.record_event(
                self._customer_phone,
                "tool_call",
                tool_name=name,
                detail={"arguments": arguments},
            )
        try:
            if name == "bakery_search_catalog":
                result = self._search_catalog(arguments)
            elif name == "bakery_create_order":
                result = self._create_order(arguments)
            elif name == "bakery_order_status":
                result = self._order_status(arguments)
            else:
                raise ValueError(f"Ferramenta da padaria não permitida: {name}")
        except Exception as exc:
            if self._audit:
                self._audit.record_event(
                    self._customer_phone,
                    "tool_error",
                    tool_name=name,
                    detail={"error_type": type(exc).__name__},
                )
            raise

        order_code = str(result.get("order_code") or "") or None
        event_type = "order_created" if name == "bakery_create_order" else "tool_result"
        if self._audit:
            self._audit.record_event(
                self._customer_phone,
                event_type,
                tool_name=name,
                order_code=order_code,
                detail={"result": result},
            )
        return result


@dataclass
class _BakerySession:
    agent: Agent
    lock: RLock = field(default_factory=RLock)


class BakeryChatService:
    """Uma sessão de IA por número remetente do WhatsApp."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        supabase_url: str,
        publishable_key: str,
        fallback_model_name: str | None = None,
        max_sessions: int = 200,
        audit: WhatsAppAuditClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._fallback = fallback_model_name
        self._url = supabase_url
        self._key = publishable_key
        self._max_sessions = max_sessions
        self._audit = audit
        self._sessions: OrderedDict[str, _BakerySession] = OrderedDict()
        self._lock = RLock()

    def _new_agent(self, sender: str) -> Agent:
        registry = BakeryToolRegistry(self._url, self._key, sender, self._audit)
        provider = GeminiProvider(
            self._api_key,
            self._model_name,
            registry.definitions,
            self._fallback,
            system_instruction=BAKERY_SYSTEM_INSTRUCTION,
        )
        return Agent(provider, registry)

    def chat(self, sender: str, message: str) -> str:
        sender = "".join(ch for ch in sender if ch.isdigit())
        if not sender:
            raise ValueError("Telefone remetente inválido")
        with self._lock:
            state = self._sessions.pop(sender, None)
            if state is None:
                state = _BakerySession(self._new_agent(sender))
            self._sessions[sender] = state
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)
        with state.lock:
            return state.agent.chat(message)
