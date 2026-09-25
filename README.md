# Pão Nosso — Plataforma Digital V4

Sistema digital da **Padaria Pão Nosso** para pedidos via Web e WhatsApp, com PostgreSQL/Supabase como fonte de verdade de catálogo, pedidos e estados.

> **Missão ativa:** `MCF-PAO-NOSSO-V4-001`  
> **Issue do produto:** #19  
> **Roadmap:** [ROADMAP.md](ROADMAP.md)  
> **Checklist:** [CHECKLIST.md](CHECKLIST.md)  
> **Arquitetura:** [docs/PAO_NOSSO_ARCHITECTURE.md](docs/PAO_NOSSO_ARCHITECTURE.md)

---

## 1. Estado atual

O fluxo principal já funciona ponta a ponta:

1. cliente monta pedido no site;
2. o pedido é persistido no Supabase;
3. recebe código `PN-XXXX`;
4. o cliente envia o código no WhatsApp;
5. o agente consulta o pedido real;
6. o agente retorna itens, total, recebimento, pagamento e status;
7. o WhatsApp também consegue criar pedidos diretamente.

A correção de identidade telefônica garante compatibilidade entre formatos do site e da Meta sem permitir consulta de pedido por telefone não relacionado.

---

## 2. Serviços e onde estão hospedados

| Serviço | Hospedagem | Endereço/identidade | Função |
|---|---|---|---|
| **Storefront Pão Nosso V3** | Vercel | https://paonosso-v3.vercel.app | cardápio, carrinho, checkout e geração PN |
| **Backend / WhatsApp / agente** | Vercel | https://meu-primeiro-agente-indol.vercel.app | FastAPI, webhook Meta, agente Pão Nosso |
| **Health backend** | Vercel | https://meu-primeiro-agente-indol.vercel.app/api/health | saúde/configuração |
| **Banco** | Supabase | projeto `paonosso-v3` | PostgreSQL, RPCs, catálogo, pedidos e ledger |
| **Região do banco** | Supabase | `sa-east-1` | região técnica do PostgreSQL |
| **WhatsApp** | Meta WhatsApp Cloud API | configurado via env | entrada e saída de mensagens |
| **IA** | Google Gemini API | configurado via env | linguagem e seleção de ferramentas |
| **Código operacional** | GitHub | `leon337/meu_primeiro_agente` | backend, migrations, docs e histórico |
| **Governança** | GitHub / MCF | `leon337/multiagent-collaboration-framework` | missão, Project Registry e gates |

### Importante

A página raiz de:

`https://meu-primeiro-agente-indol.vercel.app`

é o **Agente Executivo Pessoal (AEP)**. O mesmo deployment hospeda o endpoint WhatsApp da Pão Nosso, mas **não é o site da padaria**.

O site da padaria é:

**https://paonosso-v3.vercel.app**

Hosts `*.ts.net` ligados ao AEP/bridge também não são a loja.

---

## 3. Limite conhecido do repositório

O backend e a integração Pão Nosso/WhatsApp estão versionados aqui.

O storefront público V3 está ativo e foi verificado, porém a **fonte exata que gera `paonosso-v3.vercel.app` ainda não foi reconciliada com esta árvore Git**.

Isso é uma pendência formal da V4.0. Até a reconciliação:

- não substituir o storefront atual por uma cópia improvisada;
- não declarar o deploy do storefront reproduzível;
- localizar/exportar/versionar a fonte antes de qualquer cutover.

---

## 4. Como o sistema funciona

### Pedido iniciado no site

```text
Cliente
  │
  ▼
Pão Nosso Web / Vercel
  │
  ├── lê produtos
  │
  └── create_order(...)
           │
           ▼
   Supabase/PostgreSQL
           │
           ├── orders
           ├── order_items
           └── código PN
           │
           ▼
Mensagem preparada para WhatsApp
           │
           ▼
Meta WhatsApp Cloud API
           │
           ▼
FastAPI / Vercel
           │
           ▼
BakeryChatService + Gemini
           │
           ▼
bakery_order_status
           │
           ▼
Supabase
```

### Pedido iniciado no WhatsApp

```text
WhatsApp
  │
  ▼
Meta webhook
  │
  ▼
FastAPI
  │
  ▼
BakeryChatService
  │
  ├── bakery_search_catalog
  ├── bakery_create_order
  └── bakery_order_status
           │
           ▼
       Supabase
```

O Gemini **não é fonte de verdade** para preço, status, total ou código PN. Ele deve consultar ferramentas ligadas ao banco.

---

## 5. Dados atuais

Tabelas principais:

- `products` — catálogo;
- `orders` — cabeçalho do pedido;
- `order_items` — itens congelados no momento da compra;
- `whatsapp_conversations` — conversas;
- `whatsapp_messages` — mensagens auditadas;
- `whatsapp_events` — eventos/tool calls;
- `app_config` — configuração interna protegida.

RPCs importantes:

- `create_order`;
- `customer_order_status`;
- funções administrativas;
- funções de auditoria WhatsApp.

Migrações ficam em:

`supabase/migrations/`

---

## 6. Código Pão Nosso no repositório

### Backend do agente

- `app/bakery.py` — agente e ferramentas da padaria;
- `app/whatsapp.py` — parsing, assinatura e envio Meta;
- `app/whatsapp_audit.py` — ledger/auditoria;
- `app/server.py` — FastAPI, health e webhook.

### Banco

- `supabase/migrations/`

### MCF / contexto

- `.mcf/mission.yaml`
- `.mcf/project-capsule.yaml`
- `artifacts/phases/`

### Evolução V4

- `ROADMAP.md`
- `CHECKLIST.md`
- `docs/PAO_NOSSO_ARCHITECTURE.md`
- `docs/PAO_NOSSO_SERVICE_MAP.md`
- `docs/PAO_NOSSO_OPERATIONS.md`

---

## 7. Setup local do backend

Requer Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 -m uvicorn app.server:app --reload
```

Nunca versione `.env`.

### Testes

```bash
python3 -m pytest -q
python3 -m compileall -q app
node --check public/app.js
```

---

## 8. Variáveis de ambiente

### IA

```env
GEMINI_API_KEY=
MODEL_NAME=
FALLBACK_MODEL_NAME=
```

### WhatsApp Meta

```env
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_APP_SECRET=
WHATSAPP_GRAPH_VERSION=
```

### Pão Nosso

```env
PAONOSSO_SUPABASE_URL=
PAONOSSO_SUPABASE_KEY=
```

Pode haver variáveis adicionais do ledger/auditoria conforme a versão.

Valores reais ficam somente nos providers/ambiente seguro.

---

## 9. Webhook WhatsApp

Callback atual do backend:

```text
https://meu-primeiro-agente-indol.vercel.app/api/whatsapp/webhook
```

Requisitos:

- verify token correto;
- assinatura `X-Hub-Signature-256`;
- app secret configurado;
- message IDs deduplicados;
- outbound via Graph API.

---

## 10. Deploy

### Backend

Hospedado na Vercel.

Antes de publicar:

1. conferir branch/SHA;
2. conferir CI;
3. conferir variáveis;
4. definir rollback;
5. não expor segredos.

Depois:

1. validar `/api/health`;
2. validar webhook;
3. validar tool call;
4. validar pedido;
5. registrar evidência.

### Banco

Toda mudança estrutural deve existir como migration versionada em `supabase/migrations/`.

Fluxo:

```text
migration
→ revisão
→ aplicação autorizada
→ verificar migration live
→ smoke
→ checkpoint
```

### Storefront

Está em Vercel em `paonosso-v3.vercel.app`, mas seu pipeline só será considerado reproduzível após a reconciliação do código-fonte na V4.0.

---

## 11. Segurança

O agente Pão Nosso:

**Pode**
- consultar catálogo;
- criar pedido;
- consultar pedido usando o telefone da conversa;
- futuramente executar ações adicionais apenas por ferramentas explícitas.

**Não pode**
- acessar ferramentas executivas do AEP;
- ler arquivos locais;
- consultar pedido de outro telefone;
- inventar preço, total, status ou código;
- tratar texto de chat como confirmação de pagamento.

Merge em Git não significa deploy em produção.

---

## 12. Acompanhamento da evolução

### Roadmap

[ROADMAP.md](ROADMAP.md)

### Checklist

[CHECKLIST.md](CHECKLIST.md)

Regra:

> Uma caixa só vira `[x]` após implementação + teste + smoke + evidência.

Issues:

- #19 — missão de produto;
- #20 — V4.0 Fundação;
- #21 — V4.1 Painel;
- #22 — V4.2 WhatsApp/status;
- #23 — V4.3 Clientes;
- #24 — V4.4 Cardápio;
- #25 — V4.5 Produção;
- #26 — V4.6 Estoque;
- #27 — V4.7 Pix;
- #28 — V4.8 Entrega;
- #29 — V4.9 Analytics;
- #30 — V4.10 Agente/hardening.

---

## 13. Missão MCF

```text
MCF-PAO-NOSSO-V4-001
```

Registro MCF: `multiagent-collaboration-framework#375`.

A missão usa:

- MESTRE — coordenação;
- Sofia — arquitetura;
- Eduardo — backend;
- Manoel — PostgreSQL/Supabase;
- Beatriz — comportamento do agente;
- Ricardo — segurança;
- Júlia — governança/dados;
- Renato — validação;
- Augusto — trace;
- Carmem — documentação;
- Miriam — continuidade;
- Emily — auditoria;
- Gabriel — Git/integração;
- LÉO — gate.

---

## 14. Retomada por outro agente

Leia, nesta ordem:

1. `README.md`;
2. `CHECKLIST.md`;
3. `ROADMAP.md`;
4. `.mcf/project-capsule.yaml`;
5. `.mcf/mission.yaml`;
6. issue da fase atual;
7. provider/GitHub live.

Nunca use um status histórico como prova de produção atual.
