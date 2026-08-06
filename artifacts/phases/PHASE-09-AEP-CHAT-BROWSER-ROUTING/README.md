# PRF — PHASE-09-AEP-CHAT-BROWSER-ROUTING

Pacote de rastreabilidade da missão `MCF-AEP-002`.

## Objetivo

Conectar Web, WhatsApp e voz ao runtime executivo local por ferramentas de missão, com autorização persistente do proprietário, execução auditável, evidências no retorno e parada de emergência.

## Ordem de leitura

1. `PHASE-09-DIAGNOSIS-AND-PLAN.md` — diagnóstico, requisito e critérios;
2. `PHASE-09-IMPLEMENTATION.md` — alterações, commits e limites;
3. `PHASE-09-VALIDATION.md` — CI, falha e recuperação;
4. `mission-trace.md` — ordem real e handoffs;
5. `PHASE-09-AUDIT.md` — auditoria independente;
6. `PHASE-09-GATE.md` — decisão operacional de Léo;
7. `PHASE-09-CHECKPOINT.yaml` — estado transferível.

## Resultado atual

```yaml
chat_to_mission_routing: IMPLEMENTED
web_whatsapp_voice_shared_registry: VERIFIED
owner_authorization: IMPLEMENTED_FOR_SUPPORTED_CAPABILITIES
receipt_evidence_return: IMPLEMENTED
remote_ci: PASS
remote_whatsapp_ci: PASS
local_real_gate: READY_NOT_EXECUTED
state: WAITING_LOCAL_GATE
```

## Comando do gate autorizado

Após sincronizar a branch no notebook:

```bash
.venv/bin/python scripts/validate_aep_chat_routing_local.py
```

## Regra de conclusão

A fase não será marcada como entregue antes de uma saída local `PASS`, seguida de auditoria final e decisão de Léo sobre merge e implantação.

## Limites declarados

Este incremento não declara como concluídos:

- shell irrestrito;
- controle livre por coordenadas;
- manipulação arbitrária de todo o sistema de arquivos;
- instalação arbitrária de programas;
- validação real do desktop AT-SPI;
- smoke real da produção Web e WhatsApp.

Estado: `WAITING_LOCAL_GATE`.
