# Implementação — Fase 10

## Fluxo de aplicativos

```text
Chat/WhatsApp
  → aep_submit_mission
  → etapa channel=desktop
  → ExecutiveActionExecutor
  → SafeDesktopExecutor
  → DesktopApplicationRegistry / AtSpiDesktopBackend
  → evidência persistida no runtime
```

## Operações adicionadas

- `list_applications`: lista aplicativos gráficos registrados.
- `launch_application`: inicia um aplicativo pelo identificador `.desktop`.
- `focus_application`: focaliza uma janela por AT-SPI e usa fallback controlado de janela.

## Modelo de permissão

`AEP_DESKTOP_ALLOW_ALL_APPS=1` remove a exigência de lista nominal apenas para aplicativos gráficos registrados. Operações que alteram controles continuam passando por aprovação da etapa. Execução arbitrária de comandos não foi adicionada.

## Modo demonstrativo financeiro

Uma etapa `financial` somente pode avançar quando todos os requisitos forem verdadeiros:

1. `AEP_FINANCIAL_TEST_MODE=1`;
2. `AEP_ALLOW_DEMO_ONLY=1`;
3. `AEP_REAL_FINANCIAL_EFFECT=0`;
4. ordens reais, depósitos e saques desativados;
5. missão com `demo_only=true`;
6. etapa com `parameters.demo_only=true`;
7. domínio presente em `AEP_FINANCIAL_DEMO_DOMAINS`;
8. aprovação humana explícita.

Ações que indiquem credenciais, depósito, saque, transferência ou ordem real são bloqueadas antes da execução.

## Arquivos alterados

- `app/desktop/executor.py`
- `app/runtime/executors.py`
- `app/mcf/adapter.py`
- `app/bridge.py`
- `app/policies/engine.py`
- `app/tools/remote.py`
- `.env.example`

## Testes adicionados

- `tests/test_desktop_universal_app.py`
- `tests/test_financial_demo_policy.py`
