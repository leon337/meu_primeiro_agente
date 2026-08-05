"""Política fechada: o modelo nunca concede sua própria permissão."""

from __future__ import annotations

from urllib.parse import urlsplit

from app.missions.models import AutonomyLevel, Mission, MissionStep, RiskLevel
from app.policies.models import CapabilityClass, PolicyDecision


HUMAN_ONLY = {
    CapabilityClass.FINANCIAL,
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

        if capability in HUMAN_ONLY:
            return PolicyDecision(False, True, RiskLevel.CRITICAL, "HUMAN_ONLY", "Ação reservada exclusivamente ao humano")

        if capability in HIGH_IMPACT:
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
