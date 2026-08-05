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

## D-008 — Estado pretendido da fase

**Responsável:** Carmem  
**Estado:** AGUARDANDO AUDITORIA E GATE

A fase poderá ser encerrada como `ENTREGUE` somente após auditoria de Emily, gate de Léo, checkpoint e manifesto de integridade.
