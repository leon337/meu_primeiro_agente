# Hello Agent

Aplicação didática de terminal em Python que conversa com o Gemini e permite ao modelo solicitar apenas quatro ferramentas locais explicitamente autorizadas. O modelo roda na nuvem; as ferramentas rodam no computador sob validação da aplicação.

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
MODEL_NAME=gemini-2.5-flash
```

Crie uma chave no [Google AI Studio](https://aistudio.google.com/app/apikey). Nunca versione o `.env`.

## Uso

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
