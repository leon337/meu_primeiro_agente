# Instalação e implantação

Este guia reconstrói o ambiente sem reutilizar nenhum segredo do computador atual.

## Pré-requisitos

- Linux com systemd de usuário para a ponte permanente;
- Python 3.11 ou superior;
- conta Google AI Studio e chave Gemini;
- conta GitHub;
- projeto Vercel;
- conta pessoal Tailscale para Funnel;
- Node.js somente para usar Vercel CLI.

## Instalação Python

```bash
git clone git@github.com:leon337/meu_primeiro_agente.git
cd meu_primeiro_agente
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Preencha `.env` com valores novos. Nunca copie tokens de capturas de tela ou documentação.

## Matriz de variáveis

| Variável | Computador | Vercel | Sensível | Finalidade |
|---|---:|---:|---:|---|
| `GEMINI_API_KEY` | terminal opcional | sim | sim | API Gemini |
| `MODEL_NAME` | sim | sim | não | modelo principal |
| `FALLBACK_MODEL_NAME` | opcional | recomendado | não | fallback para 429/503 |
| `ALLOWED_DIRECTORY` | sim | não é usada pela ponte remota | não | limite de arquivos e volume |
| `APP_ACCESS_TOKEN` | opcional | sim | sim | protege chat e reset de sessão |
| `BRIDGE_URL` | não | sim | não | hostname HTTPS da ponte |
| `BRIDGE_DEVICE_TOKEN` | sim | sim | sim | autenticação Vercel → ponte |
| `WHATSAPP_VERIFY_TOKEN` | não | ao ativar | sim | handshake do webhook |
| `WHATSAPP_ACCESS_TOKEN` | não | ao ativar | sim | envio pela Graph API |
| `WHATSAPP_PHONE_NUMBER_ID` | não | ao ativar | sim | número remetente |
| `WHATSAPP_APP_SECRET` | não | ao ativar | sim | valida assinatura HMAC |
| `WHATSAPP_GRAPH_VERSION` | não | ao ativar | não | versão da Graph API |

Gere tokens longos com um gerador criptográfico. O mesmo `BRIDGE_DEVICE_TOKEN` deve existir nos dois lados.

## Execução local para desenvolvimento

Terminal:

```bash
python3 -m app.main
```

Web/PWA local:

```bash
python3 -m uvicorn app.server:app --reload
```

Ponte local:

```bash
python3 -m uvicorn app.bridge:app --host 127.0.0.1 --port 8787
```

## Vercel

Vincule o projeto e cadastre variáveis em Production e Preview:

```bash
vercel login
vercel link --yes --project meu-primeiro-agente --scope predix-ai-br
vercel env add GEMINI_API_KEY production,preview --sensitive
vercel env add APP_ACCESS_TOKEN production,preview --sensitive
vercel env add BRIDGE_DEVICE_TOKEN production,preview --sensitive
vercel env add BRIDGE_URL production,preview --no-sensitive
vercel deploy --prod --yes --scope predix-ai-br
```

Não passe segredos por `--value`; use stdin ou o prompt da CLI. Mudanças de variável só entram em uma nova implantação.

## Tailscale sem sudo

O computador atual usa o binário estático oficial em modo userspace. Para reconstruir:

1. Baixe o tarball `amd64` estável em `https://pkgs.tailscale.com/stable/`.
2. Baixe o arquivo `.sha256` correspondente e compare a soma.
3. Extraia `tailscale` e `tailscaled` em `.tools/tailscale/`.
4. Instale os serviços de usuário, ajustando os caminhos absolutos se o clone estiver em outra pasta.

```bash
mkdir -p ~/.config/systemd/user
install -m 0644 systemd/hello-agent-bridge.service ~/.config/systemd/user/
install -m 0644 systemd/hello-agent-tailscaled.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hello-agent-bridge.service hello-agent-tailscaled.service
```

Faça login no Tailscale usando o socket privado:

```bash
.tools/tailscale/tailscale \
  --socket="$PWD/.runtime/tailscaled.sock" \
  up --hostname=hello-agent-pc
```

Depois de autorizar o dispositivo no navegador, habilite Funnel:

```bash
.tools/tailscale/tailscale \
  --socket="$PWD/.runtime/tailscaled.sock" \
  funnel --bg --yes 8787
```

O primeiro uso abre uma página para habilitar HTTPS e a política Funnel. O hostname `*.ts.net` resultante é fixo. Grave-o como `BRIDGE_URL` na Vercel e faça novo deploy.

## WhatsApp Cloud API

O código está pronto, mas a conta Meta ainda não foi configurada. Para ativar:

1. Crie ou selecione um app em Meta for Developers.
2. Adicione o produto WhatsApp.
3. Cadastre as cinco variáveis `WHATSAPP_*` na Vercel.
4. Faça novo deploy.
5. Use `https://meu-primeiro-agente-indol.vercel.app/api/whatsapp/webhook` como callback.
6. Use em “Verify token” exatamente `WHATSAPP_VERIFY_TOKEN`.
7. Assine o campo `messages`.
8. Valide primeiro com o número de teste da Meta.

O POST só aceita corpo cuja assinatura `X-Hub-Signature-256` corresponda ao `WHATSAPP_APP_SECRET`.
