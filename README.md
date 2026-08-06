# Hello Agent

Assistente em Python conectado ao Gemini, disponível no terminal, como API web, PWA instalável e por webhook da WhatsApp Cloud API. O modelo roda na nuvem; as ferramentas locais continuam limitadas a uma lista fechada.

**Produção:** https://meu-primeiro-agente-indol.vercel.app

## Documentação

- [Estado atual e passagem para outra IA](docs/PROJECT_STATE.md)
- [Arquitetura e fluxo completo](docs/ARCHITECTURE.md)
- [Instalação e implantação](docs/SETUP_AND_DEPLOYMENT.md)
- [Operação e solução de problemas](docs/OPERATIONS.md)
- [Modelo de segurança](docs/SECURITY.md)
- [Histórico de construção e decisões](docs/DECISIONS.md)
- [Instruções para agentes de IA](AGENTS.md)

## Segurança e arquitetura

O `Agent` coordena a conversa sem conhecer o Gemini. `AIProvider` define o contrato substituível do provedor. `GeminiProvider` converte esse contrato para o SDK oficial. `ToolRegistry` funciona como lista fechada: nomes ou parâmetros não previstos são recusados.

Pedidos inequívocos como “Abra o Google” ou “Acesse `https://example.com` e leia o título” passam antes por um roteador determinístico. Quando o runtime executivo está realmente disponível, eles criam uma missão persistida e auditável; perguntas conceituais continuam no Gemini. Web e WhatsApp usam exatamente a mesma regra.

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

Adicione as quatro variáveis `WHATSAPP_*` antes de ativar o webhook. A pasta `.vercel/`, o arquivo `.env` e `.env.local` são ignorados pelo Git.

## Consultar o computador pela nuvem

A aplicação nunca abre uma porta do roteador. Uma ponte local autenticada executa somente as quatro ferramentas da lista fechada, e o Tailscale Funnel encaminha HTTPS até ela por um hostname fixo.

No `.env` do computador, configure uma pasta e um token aleatório longo:

```env
ALLOWED_DIRECTORY=/caminho/absoluto/permitido
BRIDGE_DEVICE_TOKEN=um_token_longo_e_exclusivo
```

Inicie a ponte:

```bash
python3 -m app.bridge
```

Depois de autenticar o Tailscale local, publique a ponte pelo Funnel:

```bash
.tools/tailscale/tailscale --socket="$PWD/.runtime/tailscaled.sock" funnel --bg --yes 8787
```

Cadastre na Vercel e faça redeploy:

```env
BRIDGE_URL=https://nome-do-computador.sua-rede.ts.net
BRIDGE_DEVICE_TOKEN=o_mesmo_token_do_computador
```

Quando `BRIDGE_URL` não está configurada, a versão na Vercel não oferece ferramentas de sistema e nunca confunde o disco da nuvem com o computador. Consulte o guia detalhado em `docs/SETUP_AND_DEPLOYMENT.md`.

### Inicialização automática no Linux

Os arquivos em `systemd/` iniciam a ponte e o Tailscale no login, sem depender do VS Code ou de um terminal aberto. O Tailscale Funnel fornece um hostname HTTPS fixo em `*.ts.net`; cadastre esse endereço como `BRIDGE_URL` na Vercel.

```bash
systemctl --user status hello-agent-bridge.service
systemctl --user status hello-agent-tailscaled.service
systemctl --user status hello-agent-executive.service
journalctl --user -u hello-agent-tailscaled.service -f
```

O serviço usa o modo de rede em espaço do usuário e não exige instalação administrativa. O estado de autenticação fica somente em `.tools/tailscale-state/`, que é ignorado pelo Git.
