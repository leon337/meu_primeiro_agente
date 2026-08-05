# PHASE-08 — Gate operacional de Léo

```yaml
mission_id: MCF-AEP-001
phase_id: PHASE-08-MCF-TRACEABILITY-REPAIR
decision_authority: Leo
gate_decision: APPROVED_WITH_FINALIZATION
```

## Evidências consideradas

- fontes canônicas registradas;
- plano de fase Classe B;
- captura local correlacionada por SHA-256;
- AEP CI e WhatsApp Compliance CI aprovados;
- validação resumida e expandida;
- smoke ponta a ponta aprovado;
- mission trace com handoffs reais;
- relatório e decisões coerentes;
- auditoria independente ciclo 2: `PASS_WITH_FINALIZATION`.

## Critérios atendidos

- não conformidade anterior reconhecida;
- execução retrospectiva rejeitada como evidência;
- artefato verificável por agente selecionado;
- gate técnico local preservado;
- nenhum segredo exposto;
- nenhuma ação irreversível executada;
- nenhuma intervenção rotineira adicional de Leandro necessária.

## Condições finais internas

```yaml
- generate_final_sha256_manifest
- update_checkpoint_to_ENTREGUE
- update_readme_final_state
```

## Limites mantidos

```yaml
merge: NOT_AUTHORIZED_BY_THIS_GATE
systemd_installation: NOT_AUTHORIZED_BY_THIS_GATE
production_deploy: NOT_AUTHORIZED_BY_THIS_GATE
browser_unrestricted: PROHIBITED
desktop_unrestricted: PROHIBITED
credentials_in_artifacts: PROHIBITED
```

## Decisão

A fase corretiva está aprovada quanto ao conteúdo e à metodologia. Gabriel, Miriam e Carmem podem executar apenas a finalização documental reversível. Após o manifesto e o checkpoint final, o Mestre pode declarar `ENTREGUE`.
