# Hello Agent

Assistente em Python conectado ao Gemini, disponível no terminal, como API web, PWA instalável e por webhook da WhatsApp Cloud API. O modelo roda na nuvem; as ferramentas locais continuam limitadas a uma lista fechada.

## Segurança e arquitetura

O `Agent` coordena a conversa sem conhecer o Gemini. `AIProvider` define o contrato substituível do provedor. `GeminiProvider` converte esse contrato para o SDK oficial. `ToolRegistry` funciona como lista fechada: nomes ou parâmetros não previstos são recusados.

Não há execução de shell, leitura de conteúdo, escrita, exclusão nem envio de arquivos. `list_files` aceita somente caminhos relativos dentro de `ALLOWED_DIRECTORY`, bloqueia `..` e retorna apenas nome, tipo e tamanho. Cada execução autorizada é impressa com horário, nome e parâmetros.

## Preparação

Requer Python 3.11 ou superior.

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Edite `.env`:

```env
GEMINI_API_KEY=sua_chave_aqui
ALLOWED_DIRECTORY=/caminho/absoluto/para/uma/pasta
MODEL_NAME=gemini-3.6-flash
FALLBACK_MODEL_NAME=gemini-3.5-flash-lite
APP_ACCESS_TOKEN=crie_um_token_longo_e_aleatorio
```

Crie uma chave no [Google AI Studio](https://aistudio.google.com/app/apikey). Nunca versione o `.env`.

## Uso

### Terminal

Na raiz do projeto:

```bash
python3 -m app.main
```

Comandos locais: `/ajuda`, `/ferramentas` e `/sair`. Exemplos de perguntas: “Quanto espaço livre tenho?”, “Como está a memória?” ou “Liste os arquivos da pasta autorizada”.

## Testes

```bash
python3 -m pytest -q
```

Os testes usam um provedor falso e nunca chamam a API. Para adicionar outro provedor, implemente `AIProvider` em `app/providers/` e troque apenas sua construção em `app/main.py`.

### Web e PWA

Inicie a API local:

```bash
python3 -m uvicorn app.server:app --reload
```

Abra `http://localhost:8000`. No celular, use **Adicionar à tela inicial** no menu do navegador. Em produção, informe o mesmo valor de `APP_ACCESS_TOKEN` nas configurações da PWA.

Endpoints principais:

- `GET /api/health`: saúde e configuração dos canais;
- `POST /api/chat`: conversa autenticada;
- `DELETE /api/sessions/{id}`: inicia uma nova conversa;
- `GET|POST /api/whatsapp/webhook`: verificação e recebimento da Meta.

### WhatsApp Cloud API

Configure também, somente no ambiente da hospedagem:

```env
WHATSAPP_VERIFY_TOKEN=um_valor_criado_por_voce
WHATSAPP_ACCESS_TOKEN=token_fornecido_pela_meta
WHATSAPP_PHONE_NUMBER_ID=id_do_numero_na_meta
WHATSAPP_APP_SECRET=segredo_do_aplicativo_meta
WHATSAPP_GRAPH_VERSION=v23.0
```

No painel da Meta, configure a URL de callback como:

```text
https://SEU-DOMINIO/api/whatsapp/webhook
```

Use em **Verify token** exatamente o valor de `WHATSAPP_VERIFY_TOKEN` e assine o campo `messages`. A versão da Graph API é configurável para facilitar atualizações.

### Vercel

O projeto usa o runtime Python/FastAPI da Vercel. Depois de vincular o projeto, configure os segredos em Production e publique:

```bash
vercel link
vercel env add GEMINI_API_KEY production
vercel env add APP_ACCESS_TOKEN production
vercel --prod
```

Adicione as quatro variáveis `WHATSAPP_*` antes de ativar o webhook. A pasta `.vercel/` e todos os arquivos `.env` são ignorados pelo Git.
