# Operação do Agente Executivo Pessoal

## Instalação local

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-executive.txt
playwright install chromium
mkdir -p var/aep
```

## Variáveis locais

```env
AEP_DATABASE_PATH=var/aep/aep.sqlite3
AEP_CONTROL_TOKEN=gere_um_token_distinto_do_bridge
AEP_AUDIT_SIGNING_KEY=gere_outro_token
AEP_BROWSER_REAL=0
AEP_BROWSER_HEADLESS=0
AEP_BROWSER_PROFILE=var/aep/browser-profile
AEP_DESKTOP_REAL=0
AEP_DESKTOP_APPS=Brave,Visual Studio Code
```

Credenciais de sites são referenciadas, nunca incluídas na missão:

```env
AEP_CREDENTIAL_GITHUB_EMAIL=
AEP_CREDENTIAL_GITHUB_PASSWORD=
```

## Fluxo MCF

1. Criar missão.
2. Transicionar para `PLANNING`.
3. Adicionar etapas.
4. Transicionar para `READY`.
5. O daemon executa ações autorizadas.
6. Alto impacto entra em `WAITING_HUMAN`.
7. Leandro aprova ou rejeita.
8. O runtime produz recibo para o agente MCF de origem.

## Ativação gradual

Comece com `AEP_BROWSER_REAL=0` e `AEP_DESKTOP_REAL=0`. Execute missões em `dry_run`, revise evidências e ative apenas um canal por vez.

## Emergência

Pela PWA, use **Parada de emergência**. Pela CLI:

```bash
python3 -m app.executive emergency-stop MCF-AEP-001 --reason "Interrupção humana"
```

## Instalação systemd

```bash
mkdir -p ~/.config/systemd/user
cp systemd/hello-agent-executive.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hello-agent-executive.service
systemctl --user status hello-agent-executive.service
```

Ajuste o caminho do repositório no arquivo se ele não estiver em `~/Documentos/GitHub/meu_primeiro_agente`.
