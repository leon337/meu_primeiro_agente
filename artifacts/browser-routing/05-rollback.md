# Rollback — roteamento de navegador

## Escopo

A correção adiciona uma camada determinística antes do Gemini e altera o health check. Não há migração de banco, mudança de esquema persistente, rotação de token nem modificação da ponte instalada.

## Antes de merge

O rollback é simplesmente fechar o PR ou apagar a branch remota. Nenhum deploy de produção deve ser promovido a partir desta branch.

## Depois de merge, antes de produção

Reverta o commit de merge em uma nova branch e valide a Preview resultante. Não altere `BRIDGE_DEVICE_TOKEN`, `AEP_CONTROL_TOKEN`, Funnel ou serviços systemd, pois eles não fazem parte desta correção.

## Depois de eventual promoção

1. identifique o deployment de produção anterior na Vercel;
2. faça rollback pelo mecanismo de deployments da Vercel;
3. confirme `GET /api/health` e o Web Chat;
4. confirme que o webhook WhatsApp continua apontando para o domínio estável;
5. preserve os recibos existentes; não apague o banco de missões;
6. registre a causa do rollback em novo artefato e issue.

## Gatilhos de rollback

- pergunta conceitual passa a abrir navegador;
- comando explícito cria missão sem autorização/domínio adequado;
- resposta anuncia conclusão sem estado real;
- Web e WhatsApp produzem decisões diferentes;
- health anuncia capacidade sem `aep_submit_mission`;
- logs ou respostas expõem segredos;
- regressão nas ferramentas diagnósticas existentes.

## Verificação após rollback

```bash
python3 -m pytest -q
systemd-analyze verify systemd/*.service
git diff --check
```

Depois, confirme health, ponte e os canais conforme `docs/OPERATIONS.md`.
