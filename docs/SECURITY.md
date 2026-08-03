# Modelo de segurança

## Objetivo

Permitir consultas limitadas ao computador sem oferecer ao modelo uma sessão de shell ou acesso irrestrito ao sistema de arquivos.

## Fronteiras de confiança

| Fronteira | Controle atual |
|---|---|
| Usuário → chat Vercel | `APP_ACCESS_TOKEN` Bearer |
| Meta → webhook | HMAC SHA-256 com `WHATSAPP_APP_SECRET` |
| Vercel → computador | HTTPS Tailscale Funnel + `BRIDGE_DEVICE_TOKEN` |
| Modelo → ferramenta | declarações explícitas + `ToolRegistry` fechado |
| Ferramenta → arquivos | `ALLOWED_DIRECTORY` + caminhos relativos validados |

Comparações de tokens usam `secrets.compare_digest`. A ponte desabilita Swagger e ReDoc e escuta somente em loopback.

## Capacidades permitidas

- medir disco do volume autorizado;
- medir memória RAM;
- obter metadados básicos do sistema;
- listar somente nomes, tipos e tamanhos em uma árvore autorizada.

## Capacidades deliberadamente ausentes

- executar shell ou subprocessos;
- ler conteúdo de arquivos;
- escrever, editar, mover ou apagar arquivos;
- enviar arquivos ao modelo;
- instalar programas por solicitação do modelo;
- controlar teclado, mouse ou tela;
- usar câmera ou microfone;
- navegar fora de `ALLOWED_DIRECTORY`.

## Validação de caminhos

`list_files` rejeita caminhos absolutos e qualquer componente `..`. O caminho final é resolvido e precisa permanecer dentro da raiz autorizada. Links simbólicos são classificados como links e não são seguidos para leitura.

## Riscos residuais

1. **Endpoint público:** qualquer pessoa pode alcançar o hostname Funnel, embora não consiga usar a API sem o token.
2. **Token compartilhado da PWA:** quem obtiver `APP_ACCESS_TOKEN` pode conversar com o agente.
3. **Token no localStorage:** scripts executados na mesma origem poderiam lê-lo; não há scripts de terceiros atualmente.
4. **Metadados sensíveis:** nomes de arquivos e hostname podem revelar informação mesmo sem conteúdo.
5. **Prompt injection:** o modelo pode solicitar apenas funções declaradas, mas ainda pode ser induzido a listar metadados dentro da pasta permitida.
6. **Sessões em memória:** não existe isolamento forte de dados em banco nem autenticação por usuário.
7. **Disponibilidade doméstica:** queda de energia, logout, suspensão ou internet interrompem a ponte.

## Regras para evolução

Novas ferramentas devem seguir estes passos:

1. definir caso de uso e dados mínimos;
2. declarar JSON Schema com `additionalProperties: false`;
3. validar entradas antes de executar;
4. limitar caminho, volume, tempo e tamanho da resposta;
5. escrever testes positivos e negativos;
6. registrar metadados da ação sem segredo;
7. obter autorização humana específica se houver escrita, execução ou dados pessoais.

Não transforme `ToolRegistry` em um executor genérico. Uma ferramenta “run_command” anularia a principal barreira de segurança do projeto.

## Gestão de segredos

- Local: `.env`, permissões restritas e nunca versionado.
- Vercel: variáveis sensíveis por ambiente.
- Tailscale: estado em `.tools/tailscale-state/`, ignorado pelo Git.
- Navegador: somente `APP_ACCESS_TOKEN`; nunca coloque Gemini ou bridge token no cliente.

Rotacione imediatamente um segredo exibido em captura pública, log, commit ou conversa não confiável. Depois da rotação, reinicie a ponte e faça redeploy da Vercel.

## Checklist antes de tornar o repositório público

```bash
git diff --cached
git log --all -p -- .env .env.local
rg -n "(API_KEY|ACCESS_TOKEN|DEVICE_TOKEN|APP_SECRET)=" . --glob '!*.example' --glob '!docs/**'
```

Revise também histórico Git, issues, pull requests, artefatos, capturas e logs; apagar apenas o arquivo atual não remove um segredo do histórico.
