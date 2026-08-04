"""Ações declarativas permitidas para o operador web."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class BrowserOperation(StrEnum):
    NAVIGATE = "navigate"
    READ_TEXT = "read_text"
    CLICK = "click"
    FILL = "fill"
    FILL_CREDENTIAL = "fill_credential"
    SELECT = "select"
    SCREENSHOT = "screenshot"
    DOWNLOAD = "download"
    SUBMIT = "submit"


@dataclass(frozen=True, slots=True)
class BrowserAction:
    operation: BrowserOperation
    url: str = ""
    selector: str = ""
    value: str = ""
    credential_ref: str = ""
    options: dict[str, Any] = field(default_factory=dict)
