# Estado atual e passagem de contexto

Atualizado em **6 de agosto de 2026**. Este documento é o ponto de entrada para outra pessoa ou IA continuar o projeto.

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
| Branch de correção atual | `fix/aep-browser-routing-consistency` |
| Estado da correção | PR `#14`; Preview Web validado; ainda não promovida para produção |
| Vercel team | `predix-ai-br` |
| Vercel project | `meu-primeiro-agente` |

O hostname da ponte não é um segredo, mas o endpoint só aceita chamadas com `BRIDGE_DEVICE_TOKEN`. Se o repositório for tornado público, avalie remover o hostname deste documento.

## Estado comprovado

- 88 testes automatizados aprovados na branch de correção.
- Deploy de produção concluído.
- `GET /api/health` confirmou `gemini_configured: true`.
- `GET /api/health` confirmou `bridge_configured: true`.
- `GET /api/health` confirmou `bridge_connected: true`.
- Uma consulta real de disco atravessou Vercel → Tailscale → computador → ferramenta local.
- Os serviços de usuário voltaram automaticamente após uma reinicialização real.
- O Funnel voltou no mesmo hostname após reiniciar apenas o serviço Tailscale.
- WhatsApp Cloud API foi configurado e uma conversa real já consultou o espaço em disco.
- O runtime executivo, a ponte e o Tailscale estão ativos como serviços do usuário.
- Três missões reais de navegador concluíram em sites públicos sem login: `example.com`, Google e Wikipédia.
- O Preview do commit `ca4ae69` passou no health e em uma missão Web real para `example.com`.
- Uma pergunta conceitual no Preview permaneceu na rota normal e não devolveu linguagem ou ID de missão.
- A correção de roteamento determinístico ainda precisa passar pelo gate WhatsApp e revisão independente do PR antes de qualquer promoção.

## Serviços locais

| Serviço | Função |
|---|---|
| `hello-agent-bridge.service` | Executa FastAPI local em `127.0.0.1:8787` |
| `hello-agent-tailscaled.service` | Executa Tailscale 1.98.10 sem privilégios administrativos |
| `hello-agent-executive.service` | Continua e audita missões executivas persistidas |

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
- `AEP_CONTROL_TOKEN` e demais variáveis `AEP_*` do runtime;
- variáveis `WHATSAPP_*`.

Na Vercel, `BRIDGE_URL` e `BRIDGE_DEVICE_TOKEN` estão aplicadas a Production e Preview. `BRIDGE_DEVICE_TOKEN` está marcado como sensível.

## O que ainda falta

1. Validar o fluxo WhatsApp no Preview com uma mensagem real ou payload assinado controlado.
2. Só depois de revisão independente decidir sobre merge e promoção para produção.
3. Adicionar persistência externa para conversas; hoje as sessões ficam em memória e podem desaparecer quando a função Vercel reinicia.
4. Substituir o token compartilhado da PWA por autenticação individual antes de disponibilizar o app a vários usuários.
5. Criar monitoramento e alerta para ponte desconectada.

## Próxima tarefa recomendada

Concluir o gate de Preview da correção de roteamento descrito em `artifacts/browser-routing/06-handoff.md`. Não faça merge nem promoção para produção antes das evidências Web e WhatsApp.
