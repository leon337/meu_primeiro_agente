# MCF-AEP-001 — Relatório de execução das sete fases

**Data:** 4 de agosto de 2026  
**Coordenação:** Mestre  
**Autoridade humana final:** Leandro  
**Autoridade operacional delegada:** Léo  
**Branch:** `feat/aep-phase-1-mission-runtime`  
**PR:** `#4`

## Objetivo

Transformar o Hello Agent em uma base executável de Agente Executivo Pessoal, integrado ao MCF, com autonomia progressiva, voz, operação web e desktop sob política determinística.

## Loop aplicado

```text
planejar
→ implementar menor incremento seguro
→ executar testes
→ localizar falha
→ corrigir
→ repetir testes
→ documentar
→ auditar
→ gate
```

## Fase 1 — Runtime de missões

Entregue: contrato, máquina de estados, SQLite transacional, controle otimista, eventos encadeados por SHA-256, aprovações, parada de emergência e memória sem segredos.

Estado: **IMPLEMENTADA E TESTADA LOCALMENTE**.

## Fase 2 — Operador web

Entregue: executor Playwright opcional, `dry_run` padrão, allowlist, HTTPS, operações fechadas, envio condicionado a aprovação e credenciais por referência local.

Estado: **IMPLEMENTADA; EXECUÇÃO REAL DESATIVADA POR PADRÃO**.

## Fase 3 — Integração MCF

Entregue: contrato MCF → AEP, criação e consulta de missão, etapas, transições, aprovação/rejeição, emergência, recibo e relay com token separado.

Estado: **IMPLEMENTADA; REQUER CONFIGURAÇÃO EXTERNA DO TOKEN DE CONTROLE**.

## Fase 4 — Voz

Entregue: pressionar-para-falar, reconhecimento `pt-BR` quando suportado, resposta falada opcional e comandos de consulta/parada.

Estado: **MVP IMPLEMENTADO**. Aprovação de alto impacto por voz permanece proibida.

## Fase 5 — Desktop Linux

Entregue: AT-SPI, allowlist de aplicativos, foco, clique por nome acessível, preenchimento e leitura limitada; sem coordenadas livres e sem shell.

Estado: **IMPLEMENTADO; BACKEND REAL NÃO VALIDADO NESTA SESSÃO**.

## Fase 6 — Autonomia e memória

Entregue: worker contínuo, retomada de missões, limite de etapas por ciclo, parada por sinal, roteamento web/desktop, memória operacional e serviço systemd.

Estado: **IMPLEMENTADO; SERVIÇO AINDA NÃO INSTALADO NO COMPUTADOR**.

## Fase 7 — Integração, testes e auditoria

Entregue: testes, compilação, CI, documentação operacional, auditoria e gate com reservas.

Validação local:

```yaml
compileall: PASS
pytest_aep: 13_PASS
systemd_verify_local: NOT_APPLICABLE_PATH_DO_USUARIO_AUSENTE
real_browser_smoke: NOT_EXECUTED
real_desktop_smoke: NOT_EXECUTED
production_deploy: NOT_EXECUTED
```

## Achado e correção durante o loop

O primeiro ciclo permitia adicionar etapas após a missão já ter saído de `PLANNING`. O runtime foi corrigido para aceitar novas etapas somente em `PLANNING` ou `RECOVERING`, e os testes foram repetidos até `13/13 PASS`.

## Estado geral

```yaml
sete_fases_de_codigo: IMPLEMENTADAS
controle_irrestrito: NAO
shell_generico: NAO
segredos_no_modelo: NAO
execucao_real_web: DESATIVADA_POR_PADRAO
execucao_real_desktop: DESATIVADA_POR_PADRAO
merge: NAO_AUTORIZADO_ATE_CI_E_SMOKE_LOCAL
```
