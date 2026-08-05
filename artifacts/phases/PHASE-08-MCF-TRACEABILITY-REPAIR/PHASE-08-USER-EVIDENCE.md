# PHASE-08 — Evidência local fornecida por Leandro

```yaml
mission_id: MCF-AEP-001
phase_id: PHASE-08-MCF-TRACEABILITY-REPAIR
produced_by: Renato
source_actor: Leandro
source_type: screenshot_terminal
captured_at_visible: 2026-08-04T23:08:00-03:00
sha256: 61a1db6cbf124a280bc434c62254e9d9fe6572b32f942acad7b33ed5aaeda909
```

## Conteúdo verificável visível

```text
=== COMPILAÇÃO E TESTES ===
[100%]

=== MISSÃO DRY-RUN, PERSISTÊNCIA E EMERGÊNCIA ===
{"dry_run_completed_steps": 1, "dry_run_mission": "COMPLETED", "emergency_stop": "CANCELLED", "event_chain_verified": true, "idempotency": true, "receipt_verified": true}

=== PLAYWRIGHT REAL SOMENTE LEITURA ===
{"completed": 2, "mode": "real", "read_only_text_verified": true}

LOCAL_GATE_RESULT=PASS
```

## Commit submetido ao gate

`3e4dfd5f9a770968d3a675bfde1e4a4a71b3b369`

O valor completo do `validated_head` fica parcialmente encoberto pela barra inferior da área de trabalho na captura, mas o worktree foi preparado pelo script para aceitar somente a referência remota aprovada. O commit correlacionado é o head do PR no momento do teste e possui checks remotos aprovados.

## Limites da evidência

- a captura comprova a saída visível do validador local;
- não comprova instalação ou ativação do serviço systemd;
- não comprova merge;
- não comprova navegador ou desktop em modo irrestrito;
- não contém credenciais visíveis;
- o arquivo de imagem não foi inserido no repositório; seu hash foi preservado para correlação.
