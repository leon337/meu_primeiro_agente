# Pão Nosso — Mapa de Serviços e Hospedagem

Última reconciliação desta missão: 2026-09-25.

## Serviços atuais

| Componente | Provedor | Endereço/Identidade | Papel | Fonte |
|---|---|---|---|---|
| Storefront Pão Nosso V3 | Vercel | https://paonosso-v3.vercel.app | cardápio, carrinho, checkout e criação PN | código-fonte ainda não reconciliado com Git |
| Backend HTTP / webhook WhatsApp | Vercel | https://meu-primeiro-agente-indol.vercel.app | FastAPI, webhook Meta, agente Pão Nosso e RPCs | `leon337/meu_primeiro_agente` |
| Health backend | Vercel | `/api/health` | saúde/configuração sem revelar segredos | `app/server.py` |
| Banco | Supabase | projeto `paonosso-v3` / ref `iavoqcjglmnpdnuseweo` | PostgreSQL, RPCs e audit ledger | migrations + provider live |
| Região do banco | Supabase AWS region | `sa-east-1` | residência técnica do banco | provider live |
| WhatsApp | Meta WhatsApp Cloud API | configuração via env no backend | entrada/saída de mensagens | `app/whatsapp.py` |
| IA do assistente | Google Gemini API | modelo configurado por env | linguagem/orquestração das ferramentas | `app/providers/gemini_provider.py` |
| Código / issues | GitHub | `leon337/meu_primeiro_agente` | fonte operacional e histórico | GitHub |
| Governança | GitHub / MCF | `leon337/multiagent-collaboration-framework` | missão, Project Registry, gates e contexto | GitHub |

## URLs que NÃO devem ser confundidas

### Storefront
`https://paonosso-v3.vercel.app`

É a loja Pão Nosso.

### Backend/AEP
`https://meu-primeiro-agente-indol.vercel.app`

É o deploy do Agente Executivo Pessoal que também hospeda o endpoint WhatsApp da Pão Nosso. A página raiz é AEP, não a loja.

### Runtime/bridge
Hosts `*.ts.net` ligados ao AEP/bridge não são o storefront Pão Nosso e não devem ser enviados ao cliente como site da padaria.

## Variáveis de ambiente relevantes

Sem valores no Git:

### Backend/IA
- `GEMINI_API_KEY`
- `MODEL_NAME`
- `FALLBACK_MODEL_NAME`

### Meta WhatsApp
- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_APP_SECRET`
- `WHATSAPP_GRAPH_VERSION`

### Pão Nosso / Supabase
- `PAONOSSO_SUPABASE_URL`
- `PAONOSSO_SUPABASE_KEY`
- token de auditoria quando aplicável

## Health checks

### Storefront
- abrir `https://paonosso-v3.vercel.app`;
- confirmar catálogo;
- confirmar que checkout cria PN.

### Backend
- `GET https://meu-primeiro-agente-indol.vercel.app/api/health`;
- esperado: `status=ok`;
- `paonosso_whatsapp_configured=true` para canal ativo.

### Banco
- projeto deve estar `ACTIVE_HEALTHY`;
- migrations esperadas devem constar no provider;
- smoke de `customer_order_status` deve preservar isolamento por telefone.

### WhatsApp
- webhook Meta chega ao backend;
- assinatura `X-Hub-Signature-256` é validada;
- message ID é deduplicado;
- tool call produz evento no ledger.

## Deploy boundaries

- backend: Vercel, a partir do repositório operacional;
- banco: Supabase migrations;
- storefront: Vercel, mas a origem do código precisa ser reconciliada antes de a V4 declarar pipeline reproduzível;
- Meta: configuração externa; alterar callback/token é mutação de produção e exige validação/rollback.

## Pendência crítica V4.0

Localizar e versionar a fonte exata que produz `paonosso-v3.vercel.app`. Até isso ocorrer:
- não declarar storefront “reproduzível”;
- não substituir o deploy existente;
- não criar uma cópia concorrente sem plano de cutover.
