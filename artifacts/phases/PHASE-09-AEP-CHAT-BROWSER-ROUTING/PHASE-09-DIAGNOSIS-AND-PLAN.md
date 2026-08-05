# PHASE-09 — AEP Chat Browser Routing

## Missão

- `mission_id`: MCF-AEP-002
- `phase_id`: PHASE-09-AEP-CHAT-BROWSER-ROUTING
- `owner`: Mestre
- `risk_class`: B
- `state`: IN_PROGRESS

## Evidência do usuário

Após cadastrar `AEP_CONTROL_TOKEN` em Production e Preview e realizar redeploy, a interface passou a mostrar `Online • computador e runtime conectados`. Mesmo assim, ao perguntar `você consegue acessar sites`, o agente respondeu que não consegue navegar na Internet.

## Diagnóstico verificável

1. `/api/health` confirma `bridge_connected=true` e `executive_configured=true`.
2. `/api/chat` continua usando `ChatService` com `RemoteToolRegistry`.
3. `RemoteToolRegistry.definitions` retorna apenas `tool_definitions()`.
4. A lista atual contém somente:
   - `get_disk_space`;
   - `get_memory_usage`;
   - `get_system_info`;
   - `list_files`.
5. O controle executivo existe apenas nos endpoints `/api/missions/*` e não está exposto como ferramenta do chat.
6. A PWA envia todo texto comum para `/api/chat`; somente comandos de status e parada de missão usam `/api/missions/*`.
7. Portanto, o token e o runtime estão corretos, mas o roteamento conversacional para navegador ainda não foi implementado.

## Objetivo

Permitir que Web e WhatsApp transformem pedidos de navegação em missões MCF controladas, inicialmente somente leitura.

## Escopo MVP seguro

- adicionar ferramenta conversacional `browse_readonly`;
- aceitar apenas URL HTTPS;
- derivar allowlist do hostname solicitado;
- criar missão `observe` com ação `read_text`;
- manter `fill`, `click`, `download`, `submit` e credenciais fora do MVP;
- aguardar conclusão com prazo limitado;
- devolver ao modelo somente texto limitado e recibo da missão;
- reutilizar a mesma rota em Web e WhatsApp por meio do `ChatService`;
- preservar parada de emergência e trilha de auditoria.

## Fora de escopo

- login automático;
- envio de formulários;
- pagamentos;
- identidade, financeiro ou jurídico;
- controle irrestrito do desktop;
- shell genérico.

## Critérios de aceite

1. Pergunta `acesse https://example.com e leia o título` cria missão real.
2. A missão chega a `COMPLETED` no runtime local.
3. A resposta contém o texto lido e identificador da missão.
4. URL HTTP, credenciais embutidas ou domínio inválido são bloqueados.
5. Web e WhatsApp usam o mesmo mecanismo.
6. Testes unitários e integração passam em Python 3.11 e 3.12.
7. Nenhuma ação mutável é executada sem fase posterior e aprovação humana.

## Fluxo MCF previsto

Mestre → Sofia (arquitetura) → Eduardo (backend) → Ricardo (segurança) → Renato (testes) → Emily (auditoria) → Léo (gate) → Mestre.
