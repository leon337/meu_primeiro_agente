# PHASE-09 — Auditoria independente

```yaml
mission_id: MCF-AEP-002
phase_id: PHASE-09-AEP-CHAT-BROWSER-ROUTING
auditor: Emily
verdict: PASS_WITH_LOCAL_ACTIVATION_GATE
```

## Escopo auditado

- diagnóstico da incapacidade conversacional;
- ferramentas apresentadas ao Gemini;
- contrato de missão e bridge;
- autorização persistente do proprietário;
- política de alto impacto;
- proteção de segredos;
- polling e retorno de evidências;
- integração Web, WhatsApp e voz;
- testes e pipelines Python 3.11/3.12;
- falha e recuperação do primeiro ciclo;
- gate local real preparado;
- rastreabilidade ESEV.

## Evidências aprovadas

1. `RemoteToolRegistry` oferece quatro ferramentas executivas quando o runtime está configurado.
2. Web, WhatsApp e voz compartilham esse registro por `get_chat_service()`.
3. `aep_submit_mission` cria, planeja e libera missões para o daemon.
4. Somente URLs web HTTPS são aceitas pela ferramenta de alto nível.
5. Domínios e capacidades são derivados das etapas e incluídos no contrato.
6. Valores de credenciais não integram o contrato nem as declarações de ferramenta.
7. `AEP_CONTROL_TOKEN` permanece no ambiente do servidor e não é devolvido ao modelo.
8. `owner_authorized` é persistido e vinculado simultaneamente a `ChatService`, retorno `chat` e autonomia mínima 4.
9. A marca não remove o bloqueio das capacidades classificadas como `HUMAN_ONLY`.
10. Ações de alto impacto já suportadas podem prosseguir sem confirmação por etapa quando a autorização persistente é válida.
11. O pacote de resultado inclui evidências recentes e erro sanitizado.
12. O polling possui limite máximo de quinze segundos.
13. A parada de emergência permanece acessível.
14. O primeiro ciclo vermelho foi registrado e corrigido sem ocultação.
15. AEP CI e WhatsApp Compliance CI passaram em Python 3.11 e 3.12.
16. O gate local usa tokens efêmeros e ambiente temporário, sem alterar `.env` ou systemd.

## Achados

```yaml
critical: 0
high: 0
medium: 4
low: 2
```

### Médios

#### AUD-09-001 — execução local real pendente

O script está criado e validado por compilação/testes, mas ainda não foi executado no notebook de Leandro. Portanto, não existe evidência desta fase de que o Chromium local concluiu a missão real.

#### AUD-09-002 — produção Vercel → notebook pendente

O código do branch ainda não foi mesclado nem implantado na produção. O teste de unidade comprova o registro, mas não comprova tráfego real da Vercel para a bridge atual.

#### AUD-09-003 — WhatsApp real pendente

O pipeline do WhatsApp passou, mas ainda não existe mensagem real desta versão criando missão e devolvendo evidência.

#### AUD-09-004 — escopo amplo parcialmente implementado

Terminal genérico, controle por coordenadas livres, novas operações amplas de arquivos, upload e encerramento arbitrário de aplicativos não possuem executores neste incremento. O relatório de implementação declara essa diferença e não apresenta tais capacidades como concluídas.

### Baixos

#### AUD-09-005 — polling curto

Missões que ultrapassarem quinze segundos exigem consulta posterior por `aep_get_mission`. Isso é comportamento intencional para evitar manter Web ou WhatsApp bloqueados indefinidamente.

#### AUD-09-006 — planejamento depende do modelo

A qualidade dos seletores e da decomposição em etapas ainda depende da capacidade do modelo. Falhas devem aparecer como missão `FAILED` ou `BLOCKED`, com evidência e erro sanitizado.

## Segurança e coerência

```yaml
secrets_in_git: NOT_FOUND_IN_CHANGED_CODE
secret_values_in_tool_schema: PROHIBITED
embedded_credentials_in_url: BLOCKED_BY_BROWSER_EXECUTOR
owner_authorization_self_granted_by_runtime: NO
owner_authorization_bound_to_authenticated_channel: YES
emergency_stop_preserved: YES
unrestricted_shell_delivered: NO
```

## Veredito

`PASS_WITH_LOCAL_ACTIVATION_GATE`.

O incremento está coerente, testado e auditável para seguir ao gate local. Merge e deploy não devem ocorrer antes de:

1. executar `scripts/validate_aep_chat_routing_local.py` no notebook;
2. obter `result=PASS` com evidência `Example Domain`;
3. anexar a saída ao PRF;
4. revalidar o head final;
5. Léo decidir o gate de integração.
