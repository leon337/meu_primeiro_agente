# Evidências — gate real de navegador

Data: 2026-08-06
Ambiente: notebook conectado, runtime/ponte/Tailscale reais
Sites: públicos, sem login e sem envio de dados

## Serviços observados

Os três serviços estavam `active (running)`:

- `hello-agent-executive.service`;
- `hello-agent-bridge.service`;
- `hello-agent-tailscaled.service`.

A ponte continuou ouvindo em `127.0.0.1:8787`. A exposição HTTPS permaneceu sob responsabilidade do Tailscale Funnel.

## Missões reais concluídas

| Caso | Mission ID | Estado | Evidência pública do recibo |
|---|---|---|---|
| abrir e ler `example.com` | `CHAT-9eaccc93-0d6d-410a-8334-aa7fb12de30d` | `COMPLETED` | URL `https://example.com/`; texto `Example Domain` |
| abrir Google | `CHAT-09f38f8b-3189-4106-b957-8bfbe2025685` | `COMPLETED` | URL `https://www.google.com/` |
| pesquisar na Wikipédia | `CHAT-dd72b614-1852-42d8-ae31-7d41e67f139e` | `COMPLETED` | URL de busca HTTPS; corpo retornou “Resultados da pesquisa” e item “Inteligência artificial” |

O fluxo efetivamente exercitado foi:

```text
ChatService da branch
  -> roteador determinístico
  -> RemoteToolRegistry.aep_submit_mission
  -> Tailscale Funnel
  -> ponte local
  -> missão persistida
  -> daemon executivo
  -> Playwright real
  -> recibo assinado
```

## Achado e correção durante o gate

As missões concluíram, mas a primeira resposta de chat não exibiu o texto porque o parser esperava `data.text`. O recibo real provou o contrato `data.outputs[].text`. Foi escrito um teste com essa estrutura real, observado em RED e corrigido em GREEN.

A busca real também evidenciou uma consulta com palavras extras ao usar `Wikipédia` acentuado. Outro teste regressivo reproduziu e corrigiu o caso.

Não foi possível repetir o gate externo após essas duas correções porque o ambiente de execução informou limite de uso. A restrição não foi contornada. As evidências reais anteriores provam o executor e o formato do recibo; os dois contratos corrigidos estão cobertos pela suíte local final de 88 testes.

## Gate do Vercel Preview

Após a publicação da branch, a Vercel criou o Preview do commit `ca4ae69`. A implantação e os checks do GitHub concluíram com sucesso.

O Preview protegido foi acessado pelo fluxo autenticado da própria Vercel, sem desabilitar Deployment Protection:

- `GET /api/health`: HTTP 200, `status: ok`, `bridge_connected: true`, `executive_available: true` e `whatsapp_configured: true`;
- pergunta Web `Você consegue acessar sites?`: resposta afirmativa baseada na ferramenta disponível, sem criar missão;
- comando Web para abrir `https://example.com`: missão `CHAT-f699477f-ad8c-416f-bcbf-f52710885079`, estado `COMPLETED`, evidência `Example Domain`.
- pergunta conceitual sobre inteligência artificial: resposta explicativa normal, sem ID ou linguagem de missão.

O webhook real da Meta não foi silenciosamente transferido para o Preview. Portanto, o teste de uma mensagem WhatsApp real nessa implantação continua sendo um gate explícito anterior ao merge.

## Segredos e privacidade

- nenhum token aparece neste artefato;
- nenhum `.env` foi copiado para o worktree;
- nenhum cabeçalho de autenticação foi registrado;
- somente IDs de missão e conteúdo de páginas públicas foram preservados;
- não houve login, formulário, download, escrita ou exclusão.

## O que esta evidência não prova

- não prova promoção para produção;
- não substitui o teste de uma mensagem WhatsApp real no Preview;
- não autoriza merge automático.
