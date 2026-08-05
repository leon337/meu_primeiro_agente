# PHASE-09 — Gate operacional de Léo

```yaml
mission_id: MCF-AEP-002
phase_id: PHASE-09-AEP-CHAT-BROWSER-ROUTING
decision_authority: Leo
gate_decision: APPROVED_FOR_LOCAL_GATE
```

## Evidências consideradas

- diagnóstico e plano da fase;
- implementação materializada;
- mission trace com ações e commits verificáveis;
- primeiro ciclo de CI vermelho e recuperação registrada;
- AEP CI `31021462220`: PASS em Python 3.11 e 3.12;
- WhatsApp Compliance CI `31021462158`: PASS em Python 3.11 e 3.12;
- testes de ferramentas, política, canais, evidências e schema Gemini;
- auditoria independente: `PASS_WITH_LOCAL_ACTIVATION_GATE`;
- script de gate local isolado;
- ausência de merge e deploy nesta fase até o momento.

## Decisão

Está autorizada a execução local de:

```bash
.venv/bin/python scripts/validate_aep_chat_routing_local.py
```

O script pode:

- iniciar bridge e daemon temporários;
- criar banco e perfil Chromium temporários;
- gerar tokens efêmeros;
- acessar `https://example.com/` em modo real e headless;
- criar uma missão pelo mesmo executor de ferramentas utilizado pelo chat;
- devolver recibo e evidência;
- limpar os processos e arquivos temporários.

## Critério de aprovação local

A saída deve conter:

```json
{
  "gate": "AEP_CHAT_ROUTING_LOCAL",
  "status": "COMPLETED",
  "checks": {
    "mission_terminal": true,
    "mission_completed": true,
    "owner_authorized": true,
    "receipt_present": true,
    "evidence_text_verified": true
  },
  "result": "PASS"
}
```

## Limites deste gate

```yaml
merge: NOT_AUTHORIZED_YET
production_deploy: NOT_AUTHORIZED_YET
systemd_changes: NOT_REQUIRED
existing_env_changes: NOT_REQUIRED
whatsapp_live_test: NOT_AUTHORIZED_BY_THIS_GATE
financial_legal_identity_actions: NOT_AUTHORIZED
```

## Próxima decisão

Após a saída local `PASS`:

1. Renato valida e registra a evidência;
2. Emily executa auditoria final do gate;
3. Léo decide merge e implantação;
4. Mestre devolve o resultado a Leandro.

Estado: `APPROVED_FOR_LOCAL_GATE`.
