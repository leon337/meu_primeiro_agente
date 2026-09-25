# Pão Nosso — Arquitetura Atual e Alvo V4

## 1. Princípio

O Pão Nosso possui dois canais de entrada que devem operar sobre a mesma verdade transacional:

1. storefront Web;
2. WhatsApp.

O PostgreSQL/Supabase é a autoridade para catálogo, pedidos e estados. O modelo de IA nunca é autoridade para preço, total, status, disponibilidade ou código PN.

## 2. Arquitetura atual observada

```text
Cliente Web
   │
   ▼
Storefront Pão Nosso V3
Vercel: paonosso-v3.vercel.app
   │
   ├── catálogo ───────────────┐
   └── create_order RPC ───────┤
                               ▼
                     Supabase / PostgreSQL
                     projeto: paonosso-v3
                     região: sa-east-1
                               ▲
                               │
WhatsApp Cloud API ─► FastAPI/AEP backend
                     Vercel:
                     meu-primeiro-agente-indol.vercel.app
                               │
                               ▼
                     BakeryChatService / Gemini
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          catálogo RPC   create_order   order_status
                               │
                               ▼
                     WhatsApp audit ledger
```

## 3. Limites atuais

- O backend Pão Nosso/WhatsApp está versionado no repositório `leon337/meu_primeiro_agente`.
- O storefront público V3 foi verificado online, porém seu código-fonte exato **não foi localizado na árvore Git atual**. Essa reconciliação é requisito V4.0.
- O repositório também contém o AEP. A Pão Nosso reutiliza o deploy HTTP/WhatsApp, mas seu agente de padaria é isolado das ferramentas executivas.
- O Pão Nosso não deve depender do bridge local do notebook para atender pedidos.

## 4. Autoridade de dados atual

### `products`
Catálogo, preço, categoria, disponibilidade básica e ordenação.

### `orders`
Pedido, código PN, cliente, telefone, fulfillment, pagamento, status e total.

### `order_items`
Itens congelados no momento do pedido.

### `whatsapp_conversations`, `whatsapp_messages`, `whatsapp_events`
Rastreabilidade do canal e das ferramentas.

### `app_config`
Configuração interna do backend, protegida por RLS.

## 5. Arquitetura alvo V4

```text
                 ┌─────────────────┐
                 │ Storefront Web  │
                 └───────┬─────────┘
                         │
WhatsApp ─► Agent API ───┼────────────┐
                         │            │
Admin/Operação ──────────┤            ▼
                         │        Command/API layer
                         │            │
                         ▼            ▼
                   PostgreSQL / Supabase
        ┌───────────────┬───────┬───────────────┐
        ▼               ▼       ▼               ▼
     pedidos         clientes estoque        pagamentos
        │               │       │               │
        └───────────────┴──┬────┴───────────────┘
                           ▼
                     Event / Outbox
                  ┌────────┼────────┐
                  ▼        ▼        ▼
              WhatsApp produção analytics
```

## 6. Padrões arquiteturais V4

- **DB-authoritative:** IA e UIs consultam dados reais.
- **Idempotência:** webhook, pagamento e notificações não podem duplicar efeitos.
- **Event/outbox:** mutação transacional e notificação devem ser desacopladas.
- **Least privilege:** storefront, admin e agente recebem permissões distintas.
- **Audit first:** toda mutação crítica deixa evento.
- **Phone identity:** telefone brasileiro é canonicalizado uma única vez.
- **No secret in Git:** chaves ficam apenas no provider.
- **Deploy evidence:** merge não equivale a produção.
- **Backward-compatible migrations:** migrações devem permitir rollback lógico ou coexistência quando possível.

## 7. Fronteiras de segurança

O agente WhatsApp pode:
- consultar catálogo;
- criar pedido;
- consultar pedido do próprio telefone;
- futuramente alterar/cancelar dentro de regras explícitas.

Ele não pode:
- executar ferramentas do AEP;
- acessar arquivos locais;
- consultar pedido de outro telefone;
- alterar preços;
- alterar status operacional sem ferramenta autorizada;
- considerar texto do modelo como confirmação de pagamento.

## 8. Evolução de repositório

Até a reconciliação do storefront, o repositório canônico do projeto é `leon337/meu_primeiro_agente`.

Separar Pão Nosso em repositório próprio só deve ocorrer se houver migração planejada com:
- preservação do histórico relevante;
- pipeline de deploy;
- atualização do Project Registry;
- redirects/domínios;
- rollback;
- nenhuma duplicação de fonte de verdade.
