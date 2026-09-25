# Pão Nosso — Runbook Operacional

## 1. Recuperação rápida de contexto

1. Ler `README.md`.
2. Ler `CHECKLIST.md`.
3. Ler `ROADMAP.md`.
4. Ler `.mcf/project-capsule.yaml`.
5. Conferir GitHub/provider live.
6. Identificar a issue da fase em execução.

## 2. Teste mínimo do fluxo atual

### Site
1. Abrir `https://paonosso-v3.vercel.app`.
2. Adicionar item.
3. Fazer checkout.
4. Confirmar geração de `PN-XXXX`.

### Banco
Confirmar que o código existe em `orders` com itens correspondentes em `order_items`.

### WhatsApp
Enviar o PN pelo número associado ao pedido.

Esperado:
- agente encontra o pedido;
- total/itens/status correspondem ao banco;
- telefone não relacionado não consegue consultar;
- eventos aparecem no audit ledger.

## 3. Desenvolvimento local do backend

Requisitos:
- Python 3.11+;
- variáveis de ambiente locais não versionadas.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 -m uvicorn app.server:app --reload
```

Testes:

```bash
python3 -m pytest -q
python3 -m compileall -q app
node --check public/app.js
```

## 4. Banco

Migrações vivem em `supabase/migrations/`.

Regra:
1. escrever migration versionada;
2. revisar impacto;
3. testar em ambiente seguro quando disponível;
4. aplicar pelo provider autorizado;
5. verificar migrations live;
6. executar smoke;
7. registrar evidência no PRF.

Nunca editar produção sem uma migration correspondente quando a mudança for estrutural.

## 5. Backend Vercel

O backend atual é o mesmo deploy do AEP:

`https://meu-primeiro-agente-indol.vercel.app`

Antes de qualquer deploy:
- conferir branch/SHA;
- conferir CI;
- conferir envs;
- registrar rollback;
- não imprimir segredos.

Depois:
- `/api/health`;
- webhook verification;
- smoke de mensagem;
- smoke de RPC;
- registrar deployment/commit.

## 6. Storefront

Produção atual:

`https://paonosso-v3.vercel.app`

**Restrição atual:** a fonte exata do deploy ainda não está reconciliada com este Git. Portanto V4.0 proíbe substituir esse deployment até localizar/exportar/versionar a origem.

## 7. WhatsApp

Callback esperado no backend:

`https://meu-primeiro-agente-indol.vercel.app/api/whatsapp/webhook`

Requisitos:
- verify token compatível;
- app secret para assinatura;
- access token e phone number id no provider;
- assinatura obrigatória em POST;
- deduplicação de message ID.

## 8. Incidente

Em falha:
1. preservar evidência;
2. identificar camada: site, banco, backend, Meta ou IA;
3. correlacionar código PN/telefone/eventos;
4. não culpar IA antes de inspecionar tool call/result;
5. aplicar CAF;
6. validar isolamento após correção;
7. registrar no PRF.

## 9. Rollback

### Banco
Usar migration corretiva/compatível; não apagar dados de pedidos como primeira resposta.

### Backend
Retornar a deployment/SHA saudável conhecida e validar health + webhook.

### Meta
Se callback novo falhar, restaurar callback anterior somente com evidência de que o backend antigo está saudável.

### Storefront
Não há rollback reproduzível documentado até a fonte V3 ser reconciliada — pendência V4.0.

## 10. Definição de “implantado”

Uma melhoria só está implantada quando:
- código versionado;
- testes aplicáveis verdes;
- provider alvo atualizado;
- smoke real passou;
- checklist atualizado;
- checkpoint disponível;
- risco residual registrado.
