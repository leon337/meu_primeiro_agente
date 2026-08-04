# Histórico de construção e decisões

Este registro explica como o projeto chegou ao estado atual e evita que outra pessoa ou IA repita caminhos já descartados.

## 1. Agente de terminal

O projeto começou como um agente Python simples conectado ao Gemini. A primeira estrutura separou `Agent`, `AIProvider`, `GeminiProvider` e ferramentas para que o provedor pudesse ser substituído sem reescrever a orquestração.

Decisão central: o modelo não recebe acesso a shell. Ele só vê quatro funções declaradas.

## 2. Modelo e indisponibilidade

Durante testes, chamadas Gemini retornaram 503 por alta demanda. Foi adicionado `FALLBACK_MODEL_NAME`, utilizado apenas para erros 429/503. O histórico passou a remover a última entrada quando uma requisição falha, evitando contaminar conversas posteriores.

Também foi corrigido o papel de `function_response` para `user`, conforme esperado pelo fluxo do SDK.

## 3. Conversão em API e PWA

O terminal virou FastAPI e recebeu uma PWA sem framework frontend. A interface guarda apenas token do aplicativo e ID de sessão no navegador. Um parser defensivo foi adicionado porque erros HTML/texto da infraestrutura não são JSON e anteriormente apareciam como `Unexpected token`.

A PWA foi publicada na Vercel. `APP_ACCESS_TOKEN` protege os endpoints de conversa e reset.

## 4. Integração do WhatsApp

Foram implementados handshake, validação HMAC, extração de mensagens de texto e envio pela Graph API. A conta de produção foi configurada com usuário de sistema dedicado, permissão mínima de mensagens e token permanente armazenado como segredo na Vercel.

Uma mensagem real comprovou o fluxo WhatsApp → Meta → Vercel → Gemini → Tailscale → computador e retorno ao WhatsApp. O número deve ser usado no formato canônico exibido pela Meta, que pode diferir do formato digitado no cadastro.

## 5. Primeiro erro da nuvem

Ao perguntar sobre disco na Vercel, o agente podia observar o filesystem efêmero da própria função e apresentá-lo como computador do usuário. A correção foi introduzir três executores:

- `ToolRegistry` para execução local;
- `RemoteToolRegistry` para computador conectado;
- `EmptyToolRegistry` na Vercel quando não há ponte.

Assim, a nuvem nunca usa suas próprias métricas como se fossem do PC.

## 6. Ponte local autenticada

`app/bridge.py` criou dois endpoints mínimos:

- `GET /health`;
- `POST /tools/execute`.

Ambos exigem `BRIDGE_DEVICE_TOKEN`. A ponte reutiliza exatamente o mesmo registro seguro de ferramentas do terminal.

## 7. Cloudflare Quick Tunnel

Um túnel `trycloudflare.com` comprovou o fluxo completo e permitiu a primeira consulta real. Ele foi descartado como solução permanente porque:

- o hostname muda após reiniciar;
- não existe garantia de disponibilidade;
- seria necessário atualizar `BRIDGE_URL` e redeployar a Vercel a cada mudança;
- automatizar envio de token a destinos novos aumentaria o risco.

## 8. Tailscale Funnel

Como não havia domínio próprio, foi escolhido Tailscale Funnel. Ele fornece hostname HTTPS previsível `*.ts.net` e persiste a configuração. A instalação foi feita sem sudo usando binários estáticos oficiais, SHA-256 verificado e `tailscaled --tun=userspace-networking`.

O computador foi registrado como `hello-agent-pc`. O hostname atual foi cadastrado na Vercel para Production e Preview.

## 9. systemd de usuário

Foram instalados dois serviços no perfil Linux. Um reinício real confirmou que a ponte e o daemon voltam após login. Outro teste reiniciou apenas o daemon Tailscale e confirmou que o mesmo Funnel reaparece.

## 10. Estado da engenharia

O desenho atual privilegia entendimento e segurança didática, não escala:

- FastAPI síncrono e simples;
- histórico em memória;
- um computador conectado;
- token compartilhado;
- quatro ferramentas somente leitura.

As próximas evoluções devem preservar essas fronteiras até que autenticação individual, persistência e auditoria estejam prontas.

## 11. Lições do cadastro Meta

- Uma conta pessoal com restrição comercial não deve ser usada para tentar contornar a decisão da Meta. O portfólio foi administrado por outra pessoa real, autorizada e sem restrição.
- A Meta impediu a criação imediata de um usuário de sistema administrador porque o administrador humano tinha menos de sete dias. Um usuário de sistema **Employee** foi suficiente quando os ativos foram atribuídos diretamente.
- O token temporário do painel não é adequado para produção. Foi criado um token permanente do usuário de sistema com somente `whatsapp_business_messaging`.
- App, conta WhatsApp de teste, conta WhatsApp de produção e número de produção possuem identificadores diferentes. Misturá-los produz integrações que parecem configuradas, mas não respondem.
- Alterar uma variável na Vercel não altera implantações antigas; um redeploy é obrigatório.
- Segredos exibidos durante a configuração foram rotacionados antes do teste final.
