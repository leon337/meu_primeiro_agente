# AEP Executive Command Center — implementação

Base: `main@07c69ee829f91ca0ed4bf7accfd1d7b99a8aeaec`

## Escopo

- novo shell executivo responsivo;
- conversa preservada como superfície principal;
- painel contextual para missão ativa e estado do sistema;
- estados de Gemini, bridge, runtime executivo e WhatsApp;
- controles de voz, nova conversa, preferências e parada de emergência preservados;
- atualização de identidade visual e geração de cache da PWA.

## Boundary preservado

- backend FastAPI sem alteração;
- contratos `/api/chat`, `/api/health`, `/api/missions/*` sem alteração;
- nenhuma nova capacidade de ferramenta;
- nenhum segredo adicionado;
- respostas do modelo continuam inseridas por `textContent`.

## Validação

A validação canônica é o workflow `AEP CI` do pull request, que executa `node --check public/app.js`, `python -m compileall -q app` e `python -m pytest -q` em Python 3.11 e 3.12.
