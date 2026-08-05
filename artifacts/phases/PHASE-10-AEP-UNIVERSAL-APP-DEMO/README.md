# FASE 10 — Controle universal de aplicativos e modo demonstrativo

## Objetivo

Permitir que o Agente Executivo Pessoal descubra, abra e focalize aplicativos gráficos registrados no Linux, independentemente da marca do navegador, e oferecer um modo de teste financeiro demonstrativo sem efeito financeiro real.

## Autoridade

- Leandro: autoridade humana final.
- Mestre: coordenação do fluxo.
- Léo: gate operacional.

## Agentes em execução

- Leonardo: requisito e critérios de aceitação.
- Sofia: arquitetura e separação entre desktop, navegador e política.
- Eduardo: implementação do backend de aplicativos.
- Ricardo: isolamento do modo demonstrativo e proteção de credenciais.
- Renato: testes e regressão.
- Emily: auditoria independente.
- Gabriel: branch, commits, CI e PR.

## Escopo implementado

1. descoberta de aplicativos por arquivos `.desktop`;
2. listagem, abertura e foco de aplicativos registrados;
3. fallback de foco por AT-SPI, `wmctrl` e `xdotool`, sem shell;
4. opção `AEP_DESKTOP_ALLOW_ALL_APPS=1` para eliminar a lista nominal de aplicativos;
5. contrato `demo_only` persistido na missão e no recibo;
6. modo financeiro demonstrativo condicionado a flags locais e domínio explícito;
7. bloqueio permanente de depósito, saque, transferência, credenciais e ordem real;
8. confirmação humana obrigatória antes de uma ação classificada como financeira, mesmo em demonstração.

## Limites deliberados

- “Qualquer aplicativo” significa aplicativo gráfico instalado e registrado por `.desktop`.
- Aplicativos sem suporte de acessibilidade podem ser abertos e focalizados, mas controles internos podem não ser identificáveis por nome.
- Não existe execução arbitrária de shell.
- Não existe automação financeira real.
- Credenciais não são aceitas no chat nem devolvidas ao modelo.

## Branch

`feat/aep-universal-app-demo-mode`
