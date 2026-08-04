# Operação e solução de problemas

## Verificação rápida

Produção:

```bash
curl https://meu-primeiro-agente-indol.vercel.app/api/health
```

Resposta esperada no estado atual:

```json
{
  "status": "ok",
  "gemini_configured": true,
  "bridge_configured": true,
  "bridge_connected": true,
  "whatsapp_configured": true
}
```

Serviços locais:

```bash
systemctl --user status hello-agent-bridge.service --no-pager
systemctl --user status hello-agent-tailscaled.service --no-pager
```

Funnel:

```bash
.tools/tailscale/tailscale \
  --socket="$PWD/.runtime/tailscaled.sock" \
  funnel status
```

## Logs

```bash
journalctl --user -u hello-agent-bridge.service -n 100 --no-pager
journalctl --user -u hello-agent-tailscaled.service -n 100 --no-pager
```

O registro da ponte mostra nome e parâmetros de cada ferramenta, mas não deve registrar tokens.

## Reiniciar com segurança

```bash
systemctl --user restart hello-agent-bridge.service
systemctl --user restart hello-agent-tailscaled.service
```

O Funnel foi configurado com `--bg`; seu estado persiste no arquivo local do Tailscale e deve reaparecer no mesmo hostname.

## Diagnóstico por sintoma

### “Online • computador desconectado”

1. Confirme que o computador está ligado e que o usuário entrou no Linux.
2. Verifique os dois serviços systemd.
3. Rode `funnel status`.
4. Teste localmente `http://127.0.0.1:8787/health` com Bearer token.
5. Teste o hostname `*.ts.net/health` com o mesmo token.
6. Confirme `BRIDGE_URL` e `BRIDGE_DEVICE_TOKEN` na Vercel.
7. Faça redeploy após alterar variáveis.

### HTTP 401 na ponte

O token enviado não corresponde ao `.env` local. Atualize o valor sensível na Vercel ou rotacione os dois lados juntos.

### HTTP 401 no chat

Abra a engrenagem da PWA e informe o valor de `APP_ACCESS_TOKEN`. O token fica no `localStorage` desse navegador.

### HTTP 503/429 do Gemini

O provedor tenta primeiro `MODEL_NAME` e depois `FALLBACK_MODEL_NAME` somente para indisponibilidade 429/503. Verifique cota, nomes de modelo e logs da Vercel.

### Erro “Unexpected token ... is not valid JSON”

A interface atual lê a resposta como texto e tenta JSON com fallback. Se reaparecer, confirme se o navegador ainda usa um service worker antigo; recarregue sem cache ou remova os dados do site.

### A conversa esqueceu o histórico

Isso é esperado após cold start ou troca de instância Vercel. O histórico ainda não possui banco durável.

### WhatsApp mostra “Convidar para o WhatsApp”

1. Não presuma a formatação do número a partir do chip ou da agenda.
2. Abra o WhatsApp Manager e copie exatamente o número canônico exibido pela Meta.
3. No Brasil, a normalização pode fazer o número exibido diferir do formato digitado durante o cadastro.
4. Teste a partir de uma segunda conta; o número Cloud API não conversa consigo mesmo.
5. Se o formato canônico também não funcionar, confirme que o número está como registrado e que a assinatura de webhooks está ativa.

### A mensagem chega, mas o bot não responde

1. Confirme `whatsapp_configured: true` em `/api/health`.
2. Verifique se o app está inscrito no campo `messages` da conta de produção, não apenas da conta de teste.
3. Confirme que `WHATSAPP_PHONE_NUMBER_ID` pertence ao número de produção correto.
4. Confirme que o usuário de sistema possui acesso ao app e permissão **Mensagens** na conta WhatsApp.
5. Gere o token com `whatsapp_business_messaging`, atualize a Vercel e faça redeploy.
6. Consulte logs da Vercel sem imprimir cabeçalhos de autorização nem corpos contendo dados pessoais.

### O deploy tenta enviar sockets ou ferramentas locais

Confirme que `.vercelignore` contém `.runtime/`, `.tools/`, `.venv/` e arquivos `.env`.

## PWA no smartphone

1. Abra a URL de produção no navegador móvel.
2. Use “Adicionar à tela inicial” ou “Instalar aplicativo”.
3. Abra a engrenagem e salve `APP_ACCESS_TOKEN` naquele aparelho.
4. Use “Nova conversa” para apagar a sessão atual no backend e gerar outro `session_id`.

## Parada de emergência

Para interromper imediatamente o acesso ao computador:

```bash
.tools/tailscale/tailscale \
  --socket="$PWD/.runtime/tailscaled.sock" \
  funnel --https=443 off
systemctl --user stop hello-agent-bridge.service
```

Para impedir que voltem no próximo login:

```bash
systemctl --user disable hello-agent-bridge.service hello-agent-tailscaled.service
```

Depois de um incidente, rotacione `BRIDGE_DEVICE_TOKEN` localmente e na Vercel.
