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
- documentação operacional atualizada;
- nenhum merge ou promoção para produção foi feito.

## Arquivos centrais

- `app/browser_routing.py` — classificação estreita e planos de missão;
- `app/chat_service.py` — decisão anterior ao modelo, resposta e evidência;
- `app/server.py` — health coerente com a capacidade;
- `tests/test_browser_intent_routing.py` — contratos de regressão;
- `artifacts/browser-routing/` — diagnóstico, plano, testes, evidências e rollback.

## Próximos gates obrigatórios

1. revisar `git status`, diff e arquivos a staged;
2. executar varredura de segredos sem ler ou imprimir arquivos `.env`;
3. commit único e push da branch;
4. abrir PR contra `main`, sem merge;
5. aguardar a Vercel criar Preview para o commit da branch;
6. confirmar `/api/health` na Preview;
7. testar no Web da Preview:
   - `Você consegue acessar sites?`;
   - `Acesse https://example.com e leia o título.`;
   - `Explique o que é inteligência artificial.`;
8. testar WhatsApp de forma controlada contra a Preview usando webhook assinado ou ambiente de teste, sem trocar silenciosamente o webhook de produção;
9. anexar IDs/estados e resultados públicos ao PR;
10. solicitar revisão independente; não mesclar automaticamente.

## Critérios para liberar uma promoção futura

- Preview Web devolve `mission_id`, estado e `Example Domain`;
- pergunta conceitual não cria missão;
- WhatsApp segue a mesma rota e devolve estado real;
- `/api/health` mostra `bridge_connected: true` e `executive_available: true`;
- diff revisado sem segredo;
- CI verde;
- aprovação humana explícita para merge/promoção.

## Observação operacional

O ambiente bloqueou uma segunda execução externa ao atingir o limite de uso. Não contorne essa restrição. A publicação/Preview deve continuar somente quando a autorização de execução externa estiver novamente disponível.
