# Diagnóstico — roteamento de navegador do AEP

Data da investigação: 2026-08-06
Branch de trabalho: `fix/aep-browser-routing-consistency`
Base auditada: `dc86f2fd9a2dbfd719fae033ca321a21db242a53`

## Sintoma confirmado

O mesmo produto apresentou respostas incompatíveis para pedidos equivalentes:

- uma pergunta de capacidade podia afirmar que o agente acessava sites;
- uma ordem explícita para abrir `https://example.com` podia ser recusada como se não existisse navegador;
- a produção informava `executive_configured: true`, embora a conversa publicada não dispusesse das ferramentas executivas.

As reproduções foram feitas com sessões novas para não depender do histórico de conversa. Nenhuma credencial foi registrada neste artefato.

## Evidências reproduzidas antes da alteração

### Execução local

1. A pergunta `Você consegue acessar sites?` recebeu uma resposta afirmativa.
2. Na mesma versão, a ordem `Acesse https://example.com e leia o título principal da página.` recebeu uma negativa de capacidade.
3. A inspeção do registro efetivo dessa execução mostrou apenas:
   - `get_disk_space`;
   - `get_memory_usage`;
   - `get_system_info`;
   - `list_files`.

Logo, a resposta afirmativa não foi baseada na disponibilidade real do runtime.

### Produção

1. `GET /api/health` retornou HTTP 200, `status: ok`, `bridge_connected: true` e `executive_configured: true`.
2. O Web Chat autenticado recusou tanto a pergunta de capacidade quanto a ordem explícita para `example.com`.
3. O commit da `origin/main` era `07c69ee829f91ca0ed4bf7accfd1d7b99a8aeaec`.
4. Nesse commit, `app/tools/remote.py` retorna somente `tool_definitions()` e não contém `aep_submit_mission`.
5. No mesmo commit, `app/server.py` define `executive_configured` apenas pela presença de `BRIDGE_URL` e `AEP_CONTROL_TOKEN`, sem verificar se o registro expõe a ferramenta executiva.
6. Os deployments GitHub/Vercel das versões mais novas estavam classificados como `Preview`; isso não demonstra promoção para o domínio de produção.

## Causa raiz

Há duas falhas independentes que se somam.

### 1. Decisão de roteamento delegada ao modelo

`ChatService.chat()` encaminha toda mensagem diretamente a `Agent.chat()`. O agente pergunta ao Gemini e somente executa uma ferramenta se o modelo espontaneamente devolver um `tool_call`. Não existe antes disso:

- classificação determinística do pedido;
- consulta do conjunto real de ferramentas;
- resposta de capacidade fundamentada nesse conjunto;
- construção determinística de missão para ordens claras de navegação.

Portanto, duas frases semanticamente próximas podem seguir caminhos diferentes conforme a saída probabilística do modelo. O prompt melhora a intenção, mas não é um contrato executável.

### 2. Indicador de saúde não prova capacidade e produção está atrás das branches AEP

A `main` usada como referência de produção conhece a variável de controle e por isso pode anunciar `executive_configured: true`, porém não adiciona ferramentas executivas ao registro remoto. As implementações de missão e navegador existem nas branches posteriores, incluindo a base desta correção, mas seus deployments registrados eram de Preview.

Assim, o indicador de saúde produzia um falso positivo: configuração presente não significava capacidade publicada.

## Trajeto exato da falha

```text
Web ou WhatsApp
  -> ChatService.chat
  -> Agent.chat
  -> GeminiProvider.send_message
  -> texto livre do modelo OU tool_call escolhido pelo modelo
  -> RemoteToolRegistry somente se houve tool_call
```

Não havia uma etapa obrigatória entre a mensagem e o Gemini capaz de dizer: “este é um pedido explícito de navegador e `aep_submit_mission` está (ou não está) disponível”.

## O que não é causa

- O executor Playwright não é a causa primária: já há teste de sessão persistente e adaptadores de `navigate`/`read_text`.
- O Tailscale Funnel não é a causa primária: a ponte respondeu ao health check.
- O token do chat não é a causa da recusa observada: as chamadas autenticadas retornaram HTTP 200 e texto do modelo.
- A simples troca de prompt ou modelo não elimina a falha, pois continua dependendo de uma decisão probabilística.

## Limites da correção

A correção deve ser feita antes do modelo, usando a lista real de ferramentas, sem criar shell arbitrário, sem ampliar leitura/escrita de arquivos e sem expor credenciais. A promoção para produção permanece fora desta branch até a conclusão das evidências e revisão.
