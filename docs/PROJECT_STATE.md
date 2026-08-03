# Estado atual e passagem de contexto

Atualizado em **3 de agosto de 2026**. Este documento é o ponto de entrada para outra pessoa ou IA continuar o projeto.

## Resultado entregue

O Hello Agent é um assistente em português que funciona em quatro superfícies:

- terminal Python;
- API FastAPI;
- PWA responsiva, instalável em smartphone;
- webhook preparado para WhatsApp Cloud API.

A aplicação web está hospedada na Vercel e consulta o computador Linux por uma ponte local autenticada publicada através do Tailscale Funnel.

## Endereços e repositório

| Item | Valor atual |
|---|---|
| Aplicação de produção | `https://meu-primeiro-agente-indol.vercel.app` |
| Ponte permanente | `https://hello-agent-pc.tail172717.ts.net` |
| GitHub | `https://github.com/leon337/meu_primeiro_agente` |
| Branch da evolução atual | `agent/permanent-local-bridge` |
| Pull request | `https://github.com/leon337/meu_primeiro_agente/pull/2` |
| Vercel team | `predix-ai-br` |
| Vercel project | `meu-primeiro-agente` |

O hostname da ponte não é um segredo, mas o endpoint só aceita chamadas com `BRIDGE_DEVICE_TOKEN`. Se o repositório for tornado público, avalie remover o hostname deste documento.

## Estado comprovado

- 23 testes automatizados aprovados.
- Deploy de produção concluído.
- `GET /api/health` confirmou `gemini_configured: true`.
- `GET /api/health` confirmou `bridge_configured: true`.
- `GET /api/health` confirmou `bridge_connected: true`.
- Uma consulta real de disco atravessou Vercel → Tailscale → computador → ferramenta local.
- Os serviços de usuário voltaram automaticamente após uma reinicialização real.
- O Funnel voltou no mesmo hostname após reiniciar apenas o serviço Tailscale.
- WhatsApp ainda não está configurado: `whatsapp_configured: false`.

## Serviços locais

| Serviço | Função |
|---|---|
| `hello-agent-bridge.service` | Executa FastAPI local em `127.0.0.1:8787` |
| `hello-agent-tailscaled.service` | Executa Tailscale 1.98.10 sem privilégios administrativos |

Ambos são serviços systemd do usuário e iniciam quando o usuário `leo` entra na sessão Linux. Eles não dependem de VS Code ou terminal. Sem `loginctl enable-linger`, não iniciam antes do login do usuário.

O binário Tailscale, seu estado e os sockets são artefatos locais ignorados pelo Git:

```text
.tools/tailscale/
.tools/tailscale-state/
.runtime/tailscaled.sock
```

## Configuração efetiva

As variáveis abaixo existem localmente ou na Vercel, mas seus valores secretos não pertencem ao Git:

- `GEMINI_API_KEY`;
- `MODEL_NAME`;
- `FALLBACK_MODEL_NAME`;
- `ALLOWED_DIRECTORY`;
- `APP_ACCESS_TOKEN`;
- `BRIDGE_URL`;
- `BRIDGE_DEVICE_TOKEN`;
- variáveis `WHATSAPP_*` quando a integração for ativada.

Na Vercel, `BRIDGE_URL` e `BRIDGE_DEVICE_TOKEN` estão aplicadas a Production e Preview. `BRIDGE_DEVICE_TOKEN` está marcado como sensível.

## O que ainda falta

1. Revisar e mesclar o pull request atual em `main`.
2. Configurar WhatsApp Cloud API e validar mensagens reais.
3. Adicionar persistência externa para conversas; hoje as sessões ficam em memória e podem desaparecer quando a função Vercel reinicia.
4. Substituir o token compartilhado da PWA por autenticação individual antes de disponibilizar o app a vários usuários.
5. Criar monitoramento e alerta para ponte desconectada.

## Próxima tarefa recomendada

Integrar WhatsApp em ambiente de teste da Meta, começando pelas variáveis descritas em `docs/SETUP_AND_DEPLOYMENT.md`. Não altere a ponte local para executar novas capacidades durante essa etapa.
