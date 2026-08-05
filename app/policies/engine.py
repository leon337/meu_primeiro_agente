"""Política determinística: o modelo nunca concede sua própria permissão."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from app.missions.models import AutonomyLevel, Mission, MissionStep, RiskLevel
from app.policies.models import CapabilityClass, PolicyDecision


HUMAN_ONLY = {
    CapabilityClass.LEGAL,
    CapabilityClass.IDENTITY_SECURITY,
    CapabilityClass.SHELL,
    CapabilityClass.CREDENTIAL_ACCESS,
}

HIGH_IMPACT = {
    CapabilityClass.COMMUNICATE,
    CapabilityClass.PUBLISH,
    CapabilityClass.INSTALL,
    CapabilityClass.DELETE,
}

REAL_FINANCIAL_ACTIONS = {
    "add_payment_method",
    "buy",
    "confirm_deposit",
    "confirm_real_order",
    "confirm_transfer",
    "confirm_withdrawal",
    "deposit",
    "fill_credential",
    "purchase_real",
    "sell",
    "sell_real",
    "submit_real_order",
    "transfer",
    "withdraw",
    "withdrawal",
}


class PolicyEngine:
    def evaluate(self, mission: Mission, step: MissionStep) -> PolicyDecision:
        try:
            capability = CapabilityClass(step.capability)
        except ValueError:
            return PolicyDecision(False, False, RiskLevel.HIGH, "UNKNOWN_CAPABILITY", "Capacidade não reconhecida")

        if step.action in mission.forbidden_actions:
            return PolicyDecision(False, False, RiskLevel.CRITICAL, "EXPLICITLY_FORBIDDEN", "Ação proibida pelo contrato")

        domain = self._domain(step.target)
        if domain and not self._domain_allowed(domain, mission.allowed_domains):
            return PolicyDecision(False, False, RiskLevel.HIGH, "DOMAIN_NOT_ALLOWED", "Domínio fora da lista permitida")

        if capability == CapabilityClass.FINANCIAL:
            return self._financial_demo(mission, step, domain)

        if capability in HUMAN_ONLY:
            return PolicyDecision(False, True, RiskLevel.CRITICAL, "HUMAN_ONLY", "Ação reservada exclusivamente ao humano")

        if capability in HIGH_IMPACT:
            if self._owner_authorized(mission) and mission.max_autonomy >= AutonomyLevel.CONFIRM_HIGH_IMPACT:
                return PolicyDecision(
                    True,
                    False,
                    RiskLevel.HIGH,
                    "OWNER_AUTHORIZED",
                    "Ação abrangida pela autorização persistente do proprietário",
                )
            return PolicyDecision(True, True, RiskLevel.HIGH, "HUMAN_CONFIRMATION", "Confirmação humana obrigatória")

        required = {
            CapabilityClass.OBSERVE: AutonomyLevel.OBSERVE,
            CapabilityClass.PREPARE: AutonomyLevel.PREPARE,
            CapabilityClass.EXECUTE_REVERSIBLE: AutonomyLevel.EXECUTE_REVERSIBLE,
        }[capability]
        if mission.max_autonomy < required:
            return PolicyDecision(False, True, RiskLevel.MEDIUM, "AUTONOMY_TOO_LOW", "Nível de autonomia insuficiente")

        risk = RiskLevel.LOW if capability == CapabilityClass.OBSERVE else RiskLevel.MEDIUM
        return PolicyDecision(True, False, risk, "ALLOWED", "Ação autorizada pela política")

    def _financial_demo(self, mission: Mission, step: MissionStep, domain: str) -> PolicyDecision:
        action = step.action.casefold().strip()
        if action in REAL_FINANCIAL_ACTIONS or step.parameters.get("real_financial_effect") is True:
            return PolicyDecision(
                False,
                True,
                RiskLevel.CRITICAL,
                "REAL_FINANCIAL_EFFECT_BLOCKED",
                "Operação com possível efeito financeiro real permanece bloqueada",
            )

        flags_ok = (
            os.getenv("AEP_FINANCIAL_TEST_MODE", "0") == "1"
            and os.getenv("AEP_ALLOW_DEMO_ONLY", "0") == "1"
            and os.getenv("AEP_REAL_FINANCIAL_EFFECT", "0") == "0"
            and os.getenv("AEP_ALLOW_REAL_ORDER", "0") == "0"
            and os.getenv("AEP_ALLOW_DEPOSIT", "0") == "0"
            and os.getenv("AEP_ALLOW_WITHDRAWAL", "0") == "0"
        )
        if not flags_ok:
            return PolicyDecision(
                False,
                True,
                RiskLevel.CRITICAL,
                "FINANCIAL_DEMO_DISABLED",
                "Modo financeiro demonstrativo não está configurado de forma isolada",
            )

        if mission.metadata.get("demo_only") is not True or step.parameters.get("demo_only") is not True:
            return PolicyDecision(
                False,
                True,
                RiskLevel.CRITICAL,
                "DEMO_SCOPE_REQUIRED",
                "Missão e etapa precisam declarar explicitamente demo_only=true",
            )

        configured_domains = tuple(
            item.strip().lower()
            for item in os.getenv("AEP_FINANCIAL_DEMO_DOMAINS", "").split(",")
            if item.strip()
        )
        if not domain or not self._domain_allowed(domain, configured_domains):
            return PolicyDecision(
                False,
                True,
                RiskLevel.CRITICAL,
                "FINANCIAL_DEMO_DOMAIN_BLOCKED",
                "Domínio não autorizado para teste financeiro demonstrativo",
            )

        return PolicyDecision(
            True,
            True,
            RiskLevel.HIGH,
            "FINANCIAL_DEMO_CONFIRMATION",
            "Ação permitida somente em ambiente demonstrativo e exige confirmação humana",
        )

    @staticmethod
    def _owner_authorized(mission: Mission) -> bool:
        return (
            mission.requester == "ChatService"
            and mission.return_to == "chat"
            and mission.metadata.get("owner_authorized") is True
        )

    @staticmethod
    def _domain(target: str) -> str:
        if not target:
            return ""
        parsed = urlsplit(target)
        return (parsed.hostname or "").lower()

    @staticmethod
    def _domain_allowed(domain: str, allowed_domains: tuple[str, ...]) -> bool:
        normalized = tuple(item.lower().strip(".") for item in allowed_domains)
        return any(domain == item or domain.endswith("." + item) for item in normalized)
