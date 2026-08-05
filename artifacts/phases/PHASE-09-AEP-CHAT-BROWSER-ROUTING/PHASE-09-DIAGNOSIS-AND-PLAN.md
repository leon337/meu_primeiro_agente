# PHASE-09 — AEP Chat, Browser e Desktop com Autonomia Integral

## Missão

- `mission_id`: MCF-AEP-002
- `phase_id`: PHASE-09-AEP-CHAT-BROWSER-ROUTING
- `owner`: Mestre
- `human_authority`: Leandro
- `risk_class`: C
- `state`: IN_PROGRESS

## Evidência do usuário

Após cadastrar `AEP_CONTROL_TOKEN` em Production e Preview e realizar redeploy, a interface passou a mostrar `Online • computador e runtime conectados`. Mesmo assim, ao perguntar `você consegue acessar sites`, o agente respondeu que não consegue navegar na Internet.

Em 05/08/2026, Leandro corrigiu o requisito: o Agente Executivo Pessoal não deve ficar limitado a navegação somente leitura nem exigir aprovação específica para login, clique, preenchimento ou envio. O proprietário concederá autorização persistente para operar o próprio computador com o alcance da sessão local.

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
7. Portanto, o token e o runtime estão corretos, mas o roteamento conversacional para navegador, desktop e sistema ainda não foi implementado.

## Decisão de autoridade

A autorização do proprietário será persistente e de escopo amplo. Não haverá confirmação humana para cada clique, preenchimento, login, download, upload, envio ou operação de interface.

A autonomia será limitada apenas pelas permissões reais do Linux, pelas credenciais disponíveis, pelas proteções dos serviços externos, pelos limites técnicos do runtime e pelo comando de parada de emergência do proprietário.

## Objetivo atualizado

Permitir que Web, WhatsApp e voz transformem pedidos naturais em missões MCF capazes de operar navegador, desktop, arquivos, aplicativos e terminal no computador de Leandro, com execução real e retorno de evidências.

## Escopo funcional

- navegação para URLs HTTPS solicitadas pelo proprietário;
- leitura e interpretação de páginas;
- clique, seleção, rolagem e interação com elementos;
- preenchimento e envio de formulários;
- autenticação em contas usando o corretor local de credenciais;
- download e upload de arquivos;
- criação, leitura, edição, movimentação e exclusão de arquivos conforme as permissões da sessão local;
- abertura, uso e encerramento de aplicativos;
- controle de teclado, mouse, janelas e área de trabalho;
- execução de comandos de terminal e scripts;
- instalação e configuração de software quando as permissões do sistema permitirem;
- continuidade de tarefas em múltiplas etapas;
- operação por Web, WhatsApp e voz usando o mesmo runtime;
- recibos, logs, capturas e artefatos verificáveis do trabalho executado;
- parada de emergência sempre disponível ao proprietário.

## Modelo de credenciais

- credenciais permanecem no computador, em corretor local;
- o modelo recebe apenas referências, nunca o segredo em texto;
- o executor preenche a credencial diretamente no campo necessário;
- valores secretos não aparecem em respostas, recibos, logs ou capturas;
- sessões já autenticadas podem ser reutilizadas pelo perfil persistente do navegador.

## Controles que não interrompem a autonomia

- autenticação entre Vercel e runtime local;
- autorização persistente do proprietário;
- trilha de auditoria e recibos assinados;
- idempotência e deduplicação;
- isolamento por missão;
- timeout e recuperação de falhas;
- parada de emergência;
- registro visível dos handoffs MCF.

Esses controles não exigem aprovação por ação e não impedem login, clique, preenchimento, envio, download, upload, terminal ou controle do desktop.

## Critérios de aceite

1. `acesse um site e pesquise X` cria e executa uma missão real.
2. O agente consegue clicar, preencher e enviar formulários sem confirmação por etapa.
3. O agente consegue reutilizar sessão autenticada ou solicitar credencial ao corretor local.
4. O agente consegue baixar, enviar e manipular arquivos.
5. O agente consegue abrir e controlar aplicativos no desktop.
6. O agente consegue executar comandos e scripts no terminal dentro das permissões do usuário local.
7. Web, WhatsApp e voz usam o mesmo mecanismo executivo.
8. Toda execução produz missão, eventos, evidências e recibo.
9. A parada de emergência interrompe a missão ativa.
10. Testes unitários, integração, navegador real, desktop real e recuperação passam em Python 3.11 e 3.12.

## Fluxo MCF atualizado

Mestre → Leonardo (requisito) → Sofia (arquitetura) → Eduardo (backend) → André (cliente/voz) → Bruno (serviços locais) → Ricardo (proteção de segredos e autenticação) → Gabriel (integração) → Renato (testes) → Emily (auditoria) → Léo (gate operacional) → Mestre → Leandro.
