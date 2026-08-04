# Tutorial reproduzível: Hello Agent no WhatsApp Cloud API

Este guia registra o processo realmente executado em **3 de agosto de 2026**, incluindo os erros encontrados. Ele foi escrito para que outra pessoa ou agente de IA consiga implantar o mesmo projeto sem depender desta conversa e sem copiar credenciais do ambiente original.

## 1. Resultado esperado

Ao final, uma mensagem percorre este fluxo:

```text
WhatsApp do usuário
  → WhatsApp Cloud API / Meta
  → webhook FastAPI na Vercel
  → Gemini
  → ferramenta solicitada
  → Tailscale Funnel
  → ponte local autenticada
  → computador autorizado
  → resposta pelo mesmo caminho até o WhatsApp
```

O teste final deve incluir uma pergunta que exija ferramenta, como espaço em disco. Uma saudação comprova apenas Meta, webhook e Gemini; a consulta de disco comprova também Tailscale e ponte local.

## 2. Regras de segurança antes de começar

- Nunca coloque tokens, chaves, números de identificação privados ou arquivos `.env` no Git.
- Não envie app secret ou access token em chats, capturas de tela ou comandos que os imprimam.
- Quando copiar um segredo, transfira-o diretamente para o cofre de variáveis da hospedagem e depois substitua a área de transferência por texto comum.
- Se um app secret ou token for exibido, rotacione-o antes de continuar.
- Use uma pessoa e empresa legítimas. Não tente burlar restrições de conta da Meta.
- Conceda ao robô apenas a permissão necessária para enviar mensagens.

## 3. Pré-requisitos

- Hello Agent funcionando na Vercel;
- `GET /api/health` com Gemini configurado;
- ponte local e Tailscale Funnel funcionando, caso sejam necessárias consultas ao computador;
- conta Meta for Developers verificada por e-mail e telefone;
- portfólio empresarial sob controle de um administrador legítimo;
- número que possa receber SMS ou ligação e que será dedicado à Cloud API;
- acesso às configurações de ambiente da Vercel.

## 4. Variáveis envolvidas

Use valores novos em cada implantação:

| Variável | Origem | Segredo | Observação |
|---|---|---:|---|
| `WHATSAPP_VERIFY_TOKEN` | gerado pelo operador | sim | token aleatório para verificar o callback |
| `WHATSAPP_APP_SECRET` | configurações básicas do app Meta | sim | valida `X-Hub-Signature-256` |
| `WHATSAPP_ACCESS_TOKEN` | usuário de sistema Meta | sim | token permanente, escopo mínimo |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Manager | não | use o ID do número de produção |
| `WHATSAPP_GRAPH_VERSION` | versão usada pelo app | não | estado validado: `v26.0` |

Cadastre cada variável em **Production e Preview**. Marque verify token, app secret e access token como sensíveis; o identificador do número e a versão da API podem ser variáveis comuns. Mudanças só entram em vigor depois de uma nova implantação.

## 5. Criar o app Meta corretamente

1. Entre em Meta for Developers com a conta do administrador autorizado.
2. Crie o app com um nome neutro, por exemplo `Hello Agent`.
3. Selecione o caso de uso **Conectar-se com clientes pelo WhatsApp**.
4. Conecte o portfólio empresarial correto.
5. Conclua a criação do app e abra a personalização do caso de uso WhatsApp.

### Erro evitado: marca no nome

A Meta recusou um nome que incluía “WhatsApp”. Use o nome do produto sem marcas da Meta, salvo se você tiver autorização específica.

### Erro evitado: conta comercial restrita

Uma conta pessoal antiga possuía restrição comercial definitiva e não oferecia revisão. O caminho correto foi usar outro administrador humano real, autorizado e sem restrição. Não crie perfis falsos e não use outra identidade para disfarçar o mesmo operador.

## 6. Configurar primeiro o webhook

Antes de receber mensagens, cadastre na Vercel:

```text
WHATSAPP_VERIFY_TOKEN=<valor aleatório longo>
WHATSAPP_APP_SECRET=<segredo atual do aplicativo>
WHATSAPP_GRAPH_VERSION=v26.0
```

Faça redeploy e configure no painel Meta:

```text
URL de callback: https://SEU-DOMINIO/api/whatsapp/webhook
Token de verificação: o mesmo WHATSAPP_VERIFY_TOKEN
```

Clique em **Verificar e salvar**. Depois, assine pelo menos o campo `messages`.

O handshake é um `GET`; as mensagens chegam por `POST`. O projeto rejeita POST sem assinatura HMAC válida, portanto o app secret precisa corresponder ao app que envia o webhook.

## 7. Não misturar os ativos de teste e produção

Durante a configuração aparecem, no mínimo:

- número de teste fornecido pela Meta;
- conta WhatsApp Business de teste;
- conta WhatsApp Business de produção;
- número de produção;
- ID do app.

Cada item possui ID próprio. Copie os valores diretamente da tela correspondente e registre apenas o tipo do valor, nunca o segredo, em suas notas. Um `PHONE_NUMBER_ID` da conta de teste com token da conta de produção é uma causa comum de falha.

## 8. Registrar o número de produção

1. Abra **Etapa 2 — Configuração da produção**.
2. Preencha nome da empresa, site público e país.
3. Adicione o número dedicado.
4. Escolha SMS ou ligação e conclua a verificação.
5. Clique em **Registrar** se a tela ainda mostrar “não registrado”.
6. Ative **Assinar webhooks** para a conta de produção.
7. Copie o `Phone Number ID` exibido e salve-o como `WHATSAPP_PHONE_NUMBER_ID` na Vercel.

### Erro evitado: confiar na formatação digitada

No teste real brasileiro, a Meta exibiu o número em formato canônico diferente daquele digitado, envolvendo o nono dígito. O contato digitado manualmente apareceu como “Convidar para o WhatsApp”; o formato mostrado pelo WhatsApp Manager funcionou.

Regra geral: para testes, use exatamente o número canônico mostrado pela Meta. Não codifique uma regra universal de remover ou acrescentar dígitos.

## 9. Criar um usuário de sistema dedicado

No Business Manager:

1. Abra **Configurações → Usuários → Usuários do sistema**.
2. Crie um usuário chamado, por exemplo, `PredixBot`.
3. Escolha a função **Employee**.

### Erro evitado: exigir Admin

A Meta bloqueou a criação de usuário de sistema Admin porque o administrador humano tinha menos de sete dias no portfólio. Não foi necessário esperar: Employee funciona quando os ativos são atribuídos diretamente.

## 10. Atribuir os ativos com privilégio mínimo

Clique em **Atribuir ativos** e configure:

### Aplicativo

- selecione o app correto;
- conceda **Gerenciar app**.

### Conta do WhatsApp

- escolha a conta de produção, não a conta de teste;
- conceda somente **Mensagens — envie e responda a mensagens como a conta do WhatsApp**.

Depois de confirmar, atualize a página. Devem aparecer dois ativos: o app e a conta WhatsApp. Se a tela disser “nenhum ativo atribuído”, atualize antes de repetir; a interface pode demorar a refletir a operação.

## 11. Gerar o token permanente

1. Clique em **Gerar token** no usuário de sistema.
2. Selecione o app correto.
3. Em expiração, selecione **Nunca** para o serviço permanente.
4. Marque somente `whatsapp_business_messaging`.
5. Gere e copie o token.

Não selecione `business_management`, `whatsapp_business_management` ou permissões de publicidade sem necessidade comprovada. Um token sem expiração reduz interrupções, mas exige rotação manual e controle rigoroso.

Cadastre o valor na Vercel como variável sensível:

```text
WHATSAPP_ACCESS_TOKEN
```

Use entrada padrão ou o formulário protegido. Evite `--value`, histórico de shell e logs. Depois faça redeploy.

## 12. Verificar a implantação

Consulte:

```bash
curl https://SEU-DOMINIO/api/health
```

Resultado esperado:

```json
{
  "status": "ok",
  "gemini_configured": true,
  "bridge_configured": true,
  "bridge_connected": true,
  "whatsapp_configured": true
}
```

Se `whatsapp_configured` continuar falso, uma das quatro variáveis obrigatórias está ausente na implantação atual. Verifique o ambiente correto e faça novo deploy.

## 13. Teste de ponta a ponta

1. Use outra conta do WhatsApp; o número Cloud API não envia mensagem para si mesmo.
2. Salve o número no formato canônico exibido pela Meta.
3. Envie `Olá` e aguarde a resposta.
4. Pergunte `Qual é o espaço em disco do meu computador?`.
5. Confirme que a resposta apresenta dados reais do computador autorizado, não do pequeno filesystem da função Vercel.

Esse segundo teste prova que a ponte está conectada e que o modelo acionou uma ferramenta da lista fechada.

## 14. Preparar a publicação do app

O projeto fornece páginas públicas em:

```text
https://SEU-DOMINIO/privacy
https://SEU-DOMINIO/terms
https://SEU-DOMINIO/data-deletion
```

Nas configurações básicas do app Meta:

1. adicione o domínio da aplicação sem caminho;
2. informe a URL da política de privacidade;
3. informe a URL dos termos de serviço;
4. escolha **URL de instruções de exclusão de dados** e informe a página correspondente;
5. envie um ícone compatível;
6. escolha a categoria adequada;
7. conclua as ações necessárias e publique o app.

A verificação empresarial e a cobrança podem ser exigidas para ampliar limites ou iniciar conversas por modelos. Mensagens iniciadas pelo usuário são o primeiro teste recomendado.

## 15. Diagnóstico rápido

### Webhook verifica, mas mensagens não chegam

- confirme a assinatura do campo `messages` na conta de produção;
- confirme que o app está conectado à WABA de produção;
- confirme o modo/publicação do app para o tipo de usuário testado.

### Mensagem chega, mas não há resposta

- verifique `whatsapp_configured`;
- confirme o token do usuário de sistema;
- confirme `WHATSAPP_PHONE_NUMBER_ID`;
- consulte logs sem revelar corpos, números completos ou tokens.

### Meta retorna 401 ou 403 no envio

- token expirado, revogado ou criado para outro app;
- permissão `whatsapp_business_messaging` ausente;
- ativo WhatsApp não atribuído ao usuário de sistema.

### Meta retorna erro de número

- número de teste e produção misturados;
- formato diferente do canônico exibido no WhatsApp Manager;
- número ainda não registrado ou webhook da WABA não assinado.

### Páginas legais funcionam localmente, mas retornam HTTP 500 na Vercel

Na Vercel, arquivos em `public/**` são publicados diretamente pela CDN. Eles não devem depender de `FileResponse` dentro da função Python. Confirme primeiro as URLs com extensão, como `/privacy.html`.

Para expor os mesmos arquivos nas URLs exigidas pela Meta sem a extensão `.html`, este projeto ativa `cleanUrls` no `vercel.json`:

```json
{
  "cleanUrls": true
}
```

Depois da correção, faça uma nova implantação e teste tanto `/privacy.html` quanto `/privacy`. Um teste local que apenas lê o arquivo não prova que o roteamento da CDN na nuvem está correto.

## 16. Checklist para outra IA continuar

- [ ] Leu `AGENTS.md` e toda a documentação obrigatória.
- [ ] Não pediu nem imprimiu segredos.
- [ ] Identificou app, WABA e número de produção sem misturar os IDs.
- [ ] Preservou assinatura HMAC do webhook.
- [ ] Preservou a lista fechada de ferramentas locais.
- [ ] Usou usuário de sistema dedicado e permissão mínima.
- [ ] Cadastrou variáveis em Production e Preview.
- [ ] Fez redeploy após mudar variáveis.
- [ ] Confirmou `/api/health`.
- [ ] Testou com outro WhatsApp e com uma pergunta que usa ferramenta.
- [ ] Registrou o resultado em `PROJECT_STATE.md` sem segredos.
