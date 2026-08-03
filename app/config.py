"""Carregamento e validação da configuração."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """Indica configuração ausente ou inválida."""


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    allowed_directory: Path
    model_name: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        key = os.getenv("GEMINI_API_KEY", "").strip()
        directory = os.getenv("ALLOWED_DIRECTORY", "").strip()
        model = os.getenv("MODEL_NAME", "gemini-2.5-flash").strip()
        missing = [name for name, value in (("GEMINI_API_KEY", key), ("ALLOWED_DIRECTORY", directory), ("MODEL_NAME", model)) if not value]
        if missing:
            raise ConfigurationError("Variáveis obrigatórias ausentes: " + ", ".join(missing))
        path = Path(directory).expanduser().resolve()
        if not path.is_dir():
            raise ConfigurationError(f"ALLOWED_DIRECTORY não é uma pasta válida: {path}")
        return cls(key, path, model)

