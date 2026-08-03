# Instruções para humanos e agentes de IA

Antes de alterar o projeto, leia nesta ordem:

1. `docs/PROJECT_STATE.md` — estado real, serviços e pendências;
2. `docs/ARCHITECTURE.md` — componentes e fluxos;
3. `docs/SECURITY.md` — limites que não podem ser enfraquecidos;
4. `docs/SETUP_AND_DEPLOYMENT.md` — instalação e publicação;
5. `docs/OPERATIONS.md` — diagnóstico e recuperação;
6. `docs/DECISIONS.md` — por que a solução atual foi escolhida.

## Regras de continuidade

- Nunca publique `.env`, `.env.local`, `.tools/`, `.runtime/`, credenciais do Tailscale ou tokens da Vercel.
- Não adicione execução arbitrária de shell, leitura de conteúdo, escrita ou exclusão de arquivos sem uma nova revisão explícita de segurança.
- Preserve a lista fechada de ferramentas em `app/tools/registry.py` e a validação de caminhos em `app/tools/files.py`.
- A ponte deve continuar ouvindo apenas em `127.0.0.1:8787`; a exposição HTTPS é responsabilidade do Tailscale Funnel.
- `BRIDGE_DEVICE_TOKEN` deve ser idêntico no computador e na Vercel, mas nunca deve aparecer em documentação, commits ou logs.
- Rode `python3 -m pytest -q` e `systemd-analyze verify systemd/*.service` antes de publicar alterações relacionadas à ponte.
- O repositório local pode ser operado por ferramentas que usam metadados Git temporários. Sempre confirme branch, diff e arquivos staged antes de commit/push.

## Critérios mínimos de conclusão

Uma alteração operacional só está concluída quando:

- os testes passam;
- `GET /api/health` retorna `status: ok`;
- se envolver o computador, `bridge_configured` e `bridge_connected` são `true`;
- nenhum segredo aparece no diff;
- README, estado do projeto e runbook continuam coerentes.
