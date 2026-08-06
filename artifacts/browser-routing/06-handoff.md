# Handoff — correção de roteamento do AEP

Atualizado em: 2026-08-06
Branch: `fix/aep-browser-routing-consistency`
Base: `dc86f2fd9a2dbfd719fae033ca321a21db242a53`

## Estado atual

Implementação e validação local estão concluídas:

- causa raiz documentada;
- roteamento determinístico implementado;
- health baseado na ferramenta realmente exposta;
- Web e WhatsApp compartilham o mesmo `ChatService`;
- recibo real suportado;
- 88 testes passam;
- serviços systemd validam;
- três missões públicas reais concluíram;
- branch publicada no commit `ca4ae69`;
- PR `#14` aberto contra `main`;
- Vercel Preview com checks verdes;
- health e fluxo Web real do Preview aprovados;
- documentação operacional atualizada;
- nenhum merge ou promoção para produção foi feito.

## Arquivos centrais

- `app/browser_routing.py` — classificação estreita e planos de missão;
- `app/chat_service.py` — decisão anterior ao modelo, resposta e evidência;
- `app/server.py` — health coerente com a capacidade;
- `tests/test_browser_intent_routing.py` — contratos de regressão;
- `artifacts/browser-routing/` — diagnóstico, plano, testes, evidências e rollback.

## Próximos gates obrigatórios

1. testar WhatsApp de forma controlada contra a Preview usando webhook assinado ou ambiente de teste, sem trocar silenciosamente o webhook de produção;
2. anexar a evidência do gate WhatsApp ao PR;
3. solicitar revisão independente;
4. não mesclar nem promover automaticamente.

## Critérios para liberar uma promoção futura

- Preview Web devolve `mission_id`, estado e `Example Domain`;
- pergunta conceitual não cria missão;
- WhatsApp segue a mesma rota e devolve estado real;
- `/api/health` mostra `bridge_connected: true` e `executive_available: true`;
- diff revisado sem segredo;
- CI verde;
- aprovação humana explícita para merge/promoção.

## Observação operacional

O Preview usa Deployment Protection. A validação foi feita pelo acesso autenticado da Vercel, sem desligar essa proteção. O webhook da Meta não deve ser apontado para um link temporário sem um plano explícito de teste e restauração.
