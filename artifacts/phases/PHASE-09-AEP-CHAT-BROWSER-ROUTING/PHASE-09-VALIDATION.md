# PHASE-09 — Validação técnica e recuperação

```yaml
mission_id: MCF-AEP-002
phase_id: PHASE-09-AEP-CHAT-BROWSER-ROUTING
produced_by: Renato
state: REMOTE_PASS_LOCAL_PENDING
```

## Primeiro ciclo — FAIL

Head submetido: `c18c83c08e6d44008bba1d9a8883d9c3d2c926ad`.

Workflows:

```yaml
AEP_CI:
  run_id: 31019883282
  conclusion: failure
WHATSAPP_COMPLIANCE_CI:
  run_id: 31019883044
  conclusion: failure
```

### Falha encontrada

```text
tests/test_gemini_provider.py::test_tool_policy_requires_explicit_local_request
```

O teste de regressão exigia literalmente:

```text
somente quando o usuário pedir explicitamente
```

A nova instrução preservava a intenção, mas havia removido a frase contratual exata.

### Classificação

```yaml
failure_type: REGRESSION_CONTRACT_TEXT
functional_routing_affected: false
recoverable: true
external_effect: none
```

### Recuperação

Patrícia localizou o erro nos logs. Tiago restaurou o contrato literal e manteve a instrução executiva logo após ele.

Commit corretivo: `d7fc6c38ca97253c80e200e3545c26bb3f44e36b`.

## Incrementos validados após a recuperação

- ferramentas executivas no registro remoto;
- carregamento de `AEP_CONTROL_TOKEN` fora do modelo;
- criação e transição automática de missão;
- validação de URLs e parâmetros;
- autorização persistente do proprietário;
- política vinculada à identidade `ChatService`;
- manutenção de bloqueio para capacidades `HUMAN_ONLY`;
- polling limitado;
- evidências no recibo;
- integração do registro compartilhado de Web, WhatsApp e voz;
- compilação do gate local isolado.

## Gate remoto final

Head funcional e gate local: `6fda5ec48ea17d1c9b1af5b13c946e25cee99262`.

### AEP CI

```yaml
run_id: 31021462220
python_3_11: PASS
python_3_12: PASS
requirements_executive: PASS
compileall: PASS
javascript_syntax: PASS
legacy_gate_script_syntax: PASS
pytest: PASS
```

### WhatsApp Compliance CI

```yaml
run_id: 31021462158
python_3_11: PASS
python_3_12: PASS
requirements: PASS
compileall: PASS
pytest: PASS
source_package: PASS
```

## Testes de regressão adicionados

1. ferramentas executivas aparecem somente com runtime configurado;
2. missão passa por `CREATED → PLANNING → READY`;
3. domínios e capacidades são derivados corretamente;
4. `owner_authorized=true` chega ao contrato local;
5. `wait_seconds=0` não faz polling;
6. polling devolve recibo terminal;
7. HTTP e parâmetros secretos inesperados são recusados;
8. consulta, aprovação e parada são encaminhadas;
9. autorização persistente só vale para `ChatService → chat`;
10. capacidade `shell` continua `HUMAN_ONLY`;
11. SDK Gemini aceita todas as declarações executivas;
12. recibo contém evidência do executor;
13. Web, WhatsApp e voz recebem o mesmo registro executivo;
14. script do gate local compila e não imprime tokens deliberadamente.

## Estado da validação

```yaml
remote_code_gate: PASS
remote_whatsapp_gate: PASS
local_real_playwright_gate: PENDING
live_vercel_to_notebook_gate: PENDING
live_whatsapp_to_notebook_gate: PENDING
```

## Decisão

`REMOTE_PASS_LOCAL_PENDING`.

O código pode seguir para auditoria independente e gate de ativação local. Merge e deploy de produção ainda não são aprovados por este relatório.
