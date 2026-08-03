"""Interface de terminal do Hello Agent."""

import logging

from app.agent import Agent
from app.config import ConfigurationError, Settings
from app.providers.gemini_provider import GeminiProvider
from app.tools.registry import ToolRegistry


HELP = """Comandos:
  /ajuda       mostra esta ajuda
  /ferramentas mostra as ferramentas autorizadas
  /sair        encerra a aplicação"""


def run() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    try:
        settings = Settings.from_env()
        registry = ToolRegistry(settings.allowed_directory)
        provider = GeminiProvider(settings.gemini_api_key, settings.model_name, registry.definitions)
    except ConfigurationError as exc:
        print(f"Erro de configuração: {exc}\nCopie .env.example para .env e preencha os valores.")
        return 1
    except Exception as exc:
        print(f"Não foi possível iniciar o provedor de IA: {exc}")
        return 1

    agent = Agent(provider, registry)
    print("Hello Agent iniciado. Digite /ajuda para ver os comandos.")
    print("Ferramentas: " + ", ".join(item.name for item in registry.definitions))
    while True:
        try:
            message = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            return 0
        if message == "/sair":
            print("Até logo!")
            return 0
        if message == "/ajuda":
            print(HELP)
        elif message == "/ferramentas":
            for definition in registry.definitions:
                print(f"- {definition.name}: {definition.description}")
        elif message:
            try:
                print(f"\nAgente: {agent.chat(message)}")
            except Exception as exc:
                print(f"Erro ao conversar com o agente: {exc}")


if __name__ == "__main__":
    raise SystemExit(run())

