"""Tipos da política determinística de autonomia."""

from dataclasses import dataclass
from enum import StrEnum

from app.missions.models import RiskLevel


class CapabilityClass(StrEnum):
    OBSERVE = "observe"
    PREPARE = "prepare"
    EXECUTE_REVERSIBLE = "execute_reversible"
    COMMUNICATE = "communicate"
    PUBLISH = "publish"
    INSTALL = "install"
    DELETE = "delete"
    FINANCIAL = "financial"
    LEGAL = "legal"
    IDENTITY_SECURITY = "identity_security"
    SHELL = "shell"
    CREDENTIAL_ACCESS = "credential_access"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    risk: RiskLevel
    code: str
    reason: str
