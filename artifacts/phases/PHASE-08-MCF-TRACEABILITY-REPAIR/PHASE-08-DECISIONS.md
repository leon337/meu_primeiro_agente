# PHASE-08 — Decisões cronológicas

## D-001 — Rejeição da execução retrospectiva

**Autoridade:** Leandro  
**Estado:** APROVADA POR INSTRUÇÃO DIRETA

A execução anterior não será aceita como MCF conforme porque apresentou papéis e resultados de modo retrospectivo, sem artefatos próprios e handoffs no ponto de atuação.

## D-002 — Abertura de fase corretiva

**Responsável:** Mestre  
**Estado:** EXECUTADA

Criar `PHASE-08-MCF-TRACEABILITY-REPAIR`, Classe B, sem alterar o código já validado.

## D-003 — Fonte canônica

**Responsável:** Miriam  
**Estado:** EXECUTADA

Aplicar MCF Project Operating Instructions e MCF-DEC-051. Preservar o histórico inválido como incidente, não como evidência.

## D-004 — Seleção proporcional

**Responsável:** Mestre  
**Estado:** EXECUTADA

Selecionar somente Mestre, Miriam, Carmem, Renato, Augusto, Gabriel, Emily e Léo. Demais agentes não participam porque não possuem entrega concreta necessária nesta fase documental.

## D-005 — Aceite do gate técnico

**Responsável:** Renato  
**Estado:** APROVADO

Aceitar como evidência técnica:

- AEP CI `30967983198`: success;
- WhatsApp Compliance CI `30967983195`: success;
- captura local SHA-256 `61a1db6cbf124a280bc434c62254e9d9fe6572b32f942acad7b33ed5aaeda909`;
- `LOCAL_GATE_RESULT=PASS`;
- dry-run, persistência, recibo, cadeia de eventos, idempotência, emergency stop e Playwright somente leitura aprovados.

## D-006 — Limites operacionais

**Responsáveis:** Mestre e Renato  
**Estado:** PRESERVADOS

Não executar:

- merge;
- instalação systemd;
- deploy de produção;
- navegador irrestrito;
- desktop irrestrito;
- exposição de credenciais.

## D-007 — Regra futura de atribuição

**Responsável:** Mestre  
**Estado:** VIGENTE

Nenhuma ação será atribuída a agente sem um dos seguintes elementos verificáveis:

- consulta de ferramenta;
- arquivo criado ou alterado;
- commit;
- teste ou log;
- decisão formal registrada;
- handoff com checkpoint.

## D-008 — Auditoria ciclo 1

**Responsável:** Emily  
**Estado:** RETURN_FOR_CLOSURE

A fase foi devolvida por ausência de checkpoint, manifesto e gate.

## D-009 — Auditoria ciclo 2

**Responsável:** Emily  
**Estado:** PASS_WITH_FINALIZATION

Após criação do checkpoint, o conteúdo substantivo foi aprovado, restando apenas finalização documental.

## D-010 — Gate operacional inicial

**Responsável:** Léo  
**Estado:** APPROVED_WITH_FINALIZATION

Autorizar somente fechamento documental reversível, preservando proibição de merge, systemd e deploy.

## D-011 — Validação do head documental

**Responsável:** Renato  
**Estado:** PASS_COM_ACHADO_CORRIGIVEL

Os workflows do head documental passaram, mas `mission-trace.md`, relatório e decisões ainda registravam estado intermediário.

## D-012 — Recuperação CAF documental

**Responsáveis:** Augusto e Carmem  
**Estado:** EXECUTADA

Atualizar trace, relatório e decisões; regenerar manifesto depois das versões finais.

## D-013 — Auditoria final

**Responsável:** Emily  
**Estado:** PASS

Os critérios ESEV e PRF foram atendidos e não existem achados abertos.

## D-014 — Gate final

**Responsável:** Léo  
**Estado:** APPROVED

A fase está aprovada como correção metodológica concluída. O gate não autoriza merge, systemd ou produção.

## D-015 — Estado final

**Responsável:** Mestre  
**Estado:** ENTREGUE

O PRF está completo, o manifesto final foi regenerado e nenhuma ação executável permanece dentro desta fase.
