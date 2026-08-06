"""Roteamento determinístico e estreito para capacidades executivas de navegador."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from urllib.parse import quote_plus


@dataclass(frozen=True)
class BrowserRoute:
    kind: str
    mission: dict[str, object] | None = None


_HTTPS_URL = re.compile(r"https://[^\s<>\"]+", re.IGNORECASE)
_CAPABILITY_VERBS = ("consegue", "pode", "e capaz", "tem capacidade")
_WEB_TERMS = ("site", "internet", "web", "navegador", "navegar")
_ACTION_PREFIXES = ("abra ", "abrir ", "acesse ", "acessar ", "navegue ", "entre ")
_RESEARCH_PREFIXES = ("pesquise ", "pesquisar ", "procure ", "buscar ", "busque ")


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character)).lower().strip()


def _base_mission(message: str, steps: list[dict[str, object]], criterion: str) -> dict[str, object]:
    return {
        "objective": message.strip(),
        "steps": steps,
        "completion_criteria": [criterion],
        "forbidden_actions": ["fill_credential", "submit", "download"],
        "max_autonomy": 4,
        "wait_seconds": 15,
    }


def _browser_steps(target: str, *, read_selector: str | None = None) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = [
        {
            "action": "navigate",
            "capability": "observe",
            "target": target,
            "parameters": {"channel": "browser"},
        }
    ]
    if read_selector:
        steps.append(
            {
                "action": "read_text",
                "capability": "observe",
                "target": target,
                "parameters": {"channel": "browser", "selector": read_selector},
            }
        )
    return steps


def _research_target(message: str, plain: str) -> str:
    query = re.sub(
        r"(?is)^\s*(pesquise|pesquisar|procure|buscar|busque)\s+(na|no|em)?\s*"
        r"(wikip[eé]dia|google)?\s*(sobre|por)?\s*",
        "",
        message,
    )
    query = re.split(r"(?i)\s+e\s+(me\s+)?(traga|mostre|retorne|resuma)\b", query, maxsplit=1)[0]
    query = query.strip(" .?!") or message.strip()
    if "wikipedia" in plain:
        return f"https://pt.wikipedia.org/w/index.php?search={quote_plus(query)}"
    return f"https://www.google.com/search?q={quote_plus(query)}"


def route_browser_intent(message: str) -> BrowserRoute:
    """Classifica somente os casos inequívocos; o restante continua no provedor de IA."""

    plain = _plain(message)
    if any(verb in plain for verb in _CAPABILITY_VERBS) and any(term in plain for term in _WEB_TERMS):
        return BrowserRoute("capability")

    is_research = plain.startswith(_RESEARCH_PREFIXES)
    if is_research:
        target = _research_target(message, plain)
        return BrowserRoute(
            "browser_action",
            _base_mission(
                message,
                _browser_steps(target, read_selector="body"),
                "resultados da pesquisa devolvidos com evidência",
            ),
        )

    is_action = plain.startswith(_ACTION_PREFIXES)
    if not is_action:
        return BrowserRoute("fallback")

    if "brave" in plain:
        return BrowserRoute(
            "browser_action",
            _base_mission(
                message,
                [
                    {
                        "action": "launch_application",
                        "capability": "execute_reversible",
                        "target": "",
                        "parameters": {"channel": "desktop", "application": "Brave"},
                    }
                ],
                "aplicativo Brave aberto no computador conectado",
            ),
        )

    match = _HTTPS_URL.search(message)
    target = match.group(0).rstrip(".,;:!?)]}") if match else ""
    if not target and "google" in plain:
        target = "https://www.google.com/"
    if not target:
        return BrowserRoute("fallback")

    selector = None
    if any(term in plain for term in ("titulo", "cabecalho")):
        selector = "h1"
    elif any(term in plain for term in ("leia", "conteudo", "texto", "traga", "extraia", "resuma")):
        selector = "body"
    return BrowserRoute(
        "browser_action",
        _base_mission(
            message,
            _browser_steps(target, read_selector=selector),
            "navegação concluída com evidência do destino",
        ),
    )
