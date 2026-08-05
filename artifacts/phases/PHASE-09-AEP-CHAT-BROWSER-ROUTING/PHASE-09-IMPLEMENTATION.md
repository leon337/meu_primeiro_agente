# PHASE-09 — Relatório de implementação

```yaml
mission_id: MCF-AEP-002
phase_id: PHASE-09-AEP-CHAT-BROWSER-ROUTING
produced_by: Carmem
technical_owners:
  - Sofia
  - Eduardo
  - Tiago
state: IMPLEMENTED_AWAITING_LOCAL_GATE
risk_class: C
```

## Objetivo do incremento

Conectar os canais Web, WhatsApp e voz ao runtime executivo local, permitindo que um pedido explícito de ação no navegador ou computador seja convertido em missão persistente, executado pelo daemon e devolvido ao chat com estado, evidências e recibo.

## Diagnóstico corrigido

Antes desta fase, `RemoteToolRegistry` apresentava ao modelo somente quatro ferramentas de diagnóstico:

- `get_disk_space`;
- `get_memory_usage`;
- `get_system_info`;
- `list_files`.

O runtime de missões existia, mas não estava acessível pelo `ChatService`. Por isso, mesmo com bridge e runtime conectados, o modelo respondia que não podia navegar.

## Implementação efetiva

### Ferramentas executivas do chat

Arquivo: `app/tools/remote.py`.

Foram adicionadas:

- `aep_submit_mission`;
- `aep_get_mission`;
- `aep_approve_step`;
- `aep_emergency_stop`.

`aep_submit_mission` executa o fluxo:

```text
CREATE
→ PLANNING
→ ADD_STEPS
→ READY
→ POLL_LIMITADO
→ RESULTADO_OU_CHECKPOINT
```

A ferramenta:

- deriva domínios permitidos das URLs HTTPS;
- deriva capacidades das etapas;
- rejeita parâmetros inesperados;
- rejeita URLs web sem HTTPS;
- não recebe valores de tokens ou senhas;
- marca a missão como originada pelo canal autenticado;
- aguarda até quinze segundos por um estado terminal;
- devolve o recibo quando o runtime concluir dentro do prazo.

Commits principais:

- `8f2969f880253f9648c64c6c3724503db63235bc`;
- `397ffa1ccfc8711eac38eba6b2d92a0acc99f7ee`;
- `fc02baa6ca38fe29fbb5b22abd0f8237c1331833`.

### Integração Gemini

Arquivo: `app/providers/gemini_provider.py`.

A instrução do sistema agora determina que pedidos explícitos de ação local utilizem `aep_submit_mission`, em vez de responder apenas que o agente não possui acesso. O modelo deve informar `mission_id`, estado e evidência retornada, sem alegar conclusão antecipada.

Commits:

- `38d8ce1b0eebb3a5cb61e7543e198998fc81ee0b`;
- correção de regressão: `d7fc6c38ca97253c80e200e3545c26bb3f44e36b`.

### Autorização persistente do proprietário

Arquivos:

- `app/mcf/adapter.py`;
- `app/mcf/contracts.py`;
- `app/bridge.py`;
- `app/policies/engine.py`.

O contrato passou a aceitar `owner_authorized`. A marca é persistida no metadado da missão e só é reconhecida pela política quando coexistem:

```yaml
requester: ChatService
return_to: chat
owner_authorized: true
max_autonomy_minimum: 4
```

Para capacidades de alto impacto já suportadas pelo runtime — comunicação, publicação, instalação e exclusão — essa combinação remove a confirmação por etapa. Capacidades ainda classificadas como `HUMAN_ONLY` não foram liberadas neste incremento.

Commits:

- `de3693bac658d305f21b2a880cff2d76603af436`;
- `b916f5300ad5ce74c108b4dc52efc040135d960d`;
- `2d6dab7f1b09df81a79f2030b9f49ae2ca82b426`;
- `1ab019953ac87ef1a95141abdadaf1223d5f24a7`.

### Evidência devolvida ao canal

O pacote de resultado passou a incluir até três evidências recentes por etapa, além da contagem, estado e erro sanitizado. Isso permite devolver ao usuário o texto lido por Playwright ou outro resultado do executor.

Commit: `cd815c6789bae5044f58208db30645c219d581b6`.

### Prova de integração dos canais

Como Web, WhatsApp e voz compartilham `get_chat_service()`, foi adicionado teste que comprova que `get_tool_registry()` expõe as quatro ferramentas executivas quando `BRIDGE_URL`, `BRIDGE_DEVICE_TOKEN` e `AEP_CONTROL_TOKEN` estão presentes.

Commit: `a43db0979c5e4082187565cc54ee111b54a9bb30`.

### Gate local real

Foi criado `scripts/validate_aep_chat_routing_local.py`. O script usa ambiente isolado e executa:

```text
aep_submit_mission
→ bridge temporária
→ SQLite temporário
→ daemon temporário
→ Playwright real headless
→ leitura de example.com
→ recibo com evidência "Example Domain"
```

O script gera tokens efêmeros, não altera `.env`, não usa o serviço systemd existente e remove o ambiente temporário ao terminar.

Commits:

- `ad141f54d4d0e779177897c87c4a385c9dd093bd`;
- teste estrutural: `6fda5ec48ea17d1c9b1af5b13c946e25cee99262`.

## Testes adicionados

- `tests/test_remote_executive_tools.py`;
- `tests/test_owner_authorized_policy.py`;
- `tests/test_result_packet_evidence.py`;
- `tests/test_channel_executive_routing.py`;
- `tests/test_chat_routing_local_gate_script.py`.

## Limites materiais deste incremento

Implementado e validado remotamente:

- roteamento do chat para missões;
- Web, WhatsApp e voz usando o mesmo registro;
- ações declarativas já existentes de navegador e desktop;
- autorização persistente para capacidades suportadas;
- polling e evidência no recibo;
- parada de emergência.

Ainda não comprovado:

- execução do gate real no notebook de Leandro;
- missão real enviada pela produção Vercel ao notebook;
- resposta real de WhatsApp contendo evidência;
- backend AT-SPI real no desktop;
- terminal genérico, controle por coordenadas livres e novas operações de arquivos não existentes no runtime atual.

## Estado

`IMPLEMENTED_AWAITING_LOCAL_GATE`.
