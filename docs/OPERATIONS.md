# Operação e solução de problemas

## Verificação rápida

Produção:

```bash
curl https://meu-primeiro-agente-indol.vercel.app/api/health
```

Resposta esperada quando todos os canais e o runtime executivo estiverem configurados:

```json
{
  "status": "ok",
  "gemini_configured": true,
  "bridge_configured": true,
  "bridge_connected": true,
  "executive_configured": true,
  "executive_available": true,
  "whatsapp_configured": true
}
```

Serviços locais:

```bash
systemctl --user status hello-agent-bridge.service --no-pager
systemctl --user status hello-agent-tailscaled.service --no-pager
systemctl --user status hello-agent-executive.service --no-pager
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
journalctl --user -u hello-agent-executive.service -n 100 --no-pager
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

### O agente diz que não navega, mas a ponte está conectada

1. Consulte `/api/health` e diferencie `bridge_connected` de `executive_available`.
2. Se a ponte estiver conectada e `executive_available` for `false`, confirme `AEP_CONTROL_TOKEN` no ambiente da aplicação.
3. Confirme que o registro remoto expõe `aep_submit_mission`; presença apenas das quatro ferramentas diagnósticas não significa capacidade executiva.
4. Confirme que a versão implantada contém `app/browser_routing.py` e o roteamento em `ChatService`.
5. Teste “Você consegue acessar sites?” e depois “Acesse https://example.com e leia o título.”
6. A segunda resposta só pode declarar sucesso se trouxer `mission_id` e estado real.

### A missão conclui, mas o texto lido não aparece

O recibo real armazena resultados em `receipt.payload.steps[].evidence[].data.outputs[]`. Rode os testes de `tests/test_browser_intent_routing.py` e confirme que o parser procura `text` nesse nível, sem registrar o recibo completo.

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
systemctl --user stop hello-agent-executive.service
```

Para impedir que voltem no próximo login:

```bash
systemctl --user disable hello-agent-bridge.service hello-agent-tailscaled.service
```

Depois de um incidente, rotacione `BRIDGE_DEVICE_TOKEN` localmente e na Vercel.
