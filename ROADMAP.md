# Pão Nosso V4 — Roadmap de Evolução

> Missão MCF: `MCF-PAO-NOSSO-V4-001`  
> Issue-mãe do produto: #19  
> Issue MCF: `leon337/multiagent-collaboration-framework#375`  
> Fonte operacional: este repositório + provider live.

## Objetivo

Evoluir o Pão Nosso de um fluxo funcional de pedidos Web + WhatsApp para uma plataforma operacional de padaria, implantada em fases pequenas, testáveis e reversíveis.

## Regras do roadmap

1. Uma fase só muda para **CONCLUÍDA** quando implementação, testes, smoke e documentação estiverem registrados.
2. `CHECKLIST.md` é o painel versionado do progresso.
3. GitHub/provider live prevalece sobre documentação antiga.
4. Merge não significa deploy. Deploy deve ter evidência do provider.
5. Mudanças de produção, dados pessoais, pagamento e WhatsApp seguem gates MCF Classe C.
6. Toda fase deve deixar checkpoint retomável.

## Baseline já existente

- storefront Pão Nosso V3 recebe carrinho e checkout;
- pedido recebe código `PN-XXXX` antes do WhatsApp;
- catálogo e pedidos persistem no Supabase/PostgreSQL;
- WhatsApp consulta pedido por código + identidade telefônica equivalente;
- WhatsApp também cria pedido diretamente;
- ledger de eventos do WhatsApp existe;
- isolamento do pedido por telefone foi validado.

## Sequência de implantação

| Fase | Issue | Estado | Entrega principal | Dependências |
|---|---:|---|---|---|
| V4.0 | #20 | EM_EXECUÇÃO | Fundação, documentação, mapa de serviços e rastreabilidade | baseline |
| V4.1 | #21 | PLANEJADA | Painel operacional em tempo real | V4.0 |
| V4.2 | #22 | PLANEJADA | Status + notificações WhatsApp | V4.1 |
| V4.3 | #23 | PLANEJADA | Clientes, endereços e histórico | V4.0 |
| V4.4 | #24 | PLANEJADA | Cardápio administrável | V4.0 |
| V4.5 | #25 | PLANEJADA | Fila de produção/cozinha | V4.1 |
| V4.6 | #26 | PLANEJADA | Estoque e disponibilidade automática | V4.4, V4.5 |
| V4.7 | #27 | PLANEJADA | Pix + conciliação | V4.1, V4.2 |
| V4.8 | #28 | PLANEJADA | Entrega e logística | V4.2, V4.3 |
| V4.9 | #29 | PLANEJADA | Dashboard e analytics | V4.1–V4.8 |
| V4.10 | #30 | PLANEJADA | Agente ampliado + hardening | transversal |

## V4.0 — Fundação e mapa operacional

**Meta:** toda pessoa/agente deve conseguir recuperar o projeto, saber onde cada serviço roda e entender o que está ou não versionado.

Entregas:
- README operacional completo;
- arquitetura atual/alvo;
- mapa de serviços e hosting;
- contrato/capsule MCF;
- roadmap + checklist;
- issues por fase;
- baseline de produção registrado;
- reconciliar o código-fonte do storefront público com um repositório Git canônico.

**Saída:** nenhum componente de produção sem dono, URL/provedor conhecido e fonte de código identificada.

## V4.1 — Painel operacional

Entregas:
- visão `Novo → Confirmado → Preparando → Pronto → Entregue/Cancelado`;
- atualização de status em um clique;
- filtros por retirada/entrega/pagamento;
- tempo de espera;
- chegada de pedido em tempo real;
- UI responsiva para balcão/cozinha.

**Saída:** pedido criado pelo site ou WhatsApp aparece no painel sem refresh manual e pode percorrer o ciclo com auditoria.

## V4.2 — Status e notificações WhatsApp

Entregas:
- evento de mudança de status;
- mensagens automáticas idempotentes;
- consulta “onde está meu pedido?”;
- prevenção de envio duplicado;
- registro de delivery/status no ledger.

**Saída:** cada transição relevante produz no máximo uma notificação e o cliente recebe o estado real.

## V4.3 — Clientes e histórico

Entregas:
- entidade de cliente por identidade telefônica canônica;
- endereços reutilizáveis;
- histórico de pedidos;
- preferências explícitas;
- repetição de pedido;
- regras de retenção e acesso.

**Saída:** cliente recorrente pode repetir pedido sem misturar identidade ou expor outro cliente.

## V4.4 — Cardápio administrável

Entregas:
- CRUD de produtos;
- preço, categoria, unidade, foto e descrição;
- disponibilidade/“esgotado”;
- destaque/promoção;
- histórico mínimo de alterações.

**Saída:** operação altera cardápio sem editar código ou SQL manualmente.

## V4.5 — Fila de produção

Entregas:
- agregação de itens por janela;
- prioridade/horário;
- visão cozinha;
- preparado/pronto;
- vínculo com pedidos.

**Saída:** cozinha sabe o que produzir e quanto, derivado dos pedidos reais.

## V4.6 — Estoque

Entregas:
- saldo/disponibilidade;
- reserva/baixa;
- bloqueio de venda sem saldo;
- ajuste manual auditado;
- alerta de mínimo.

**Saída:** site e agente deixam de vender produto indisponível de forma consistente.

## V4.7 — Pix

Entregas:
- cobrança por pedido;
- QR Code/copia-e-cola;
- estado `aguardando/pago/expirado`;
- webhook idempotente;
- conciliação no pedido.

**Saída:** pagamento confirmado muda o estado sem ação manual e sem depender de texto do cliente.

## V4.8 — Entrega

Entregas:
- endereço estruturado;
- bairros/raios atendidos;
- taxa e previsão;
- atribuição de entregador;
- `saiu para entrega/entregue`.

**Saída:** pedido delivery possui custo, destino, responsável e rastreabilidade.

## V4.9 — Analytics

Entregas:
- faturamento;
- ticket médio;
- produtos;
- horários de pico;
- recorrência;
- site × WhatsApp;
- cancelamento e tempo de ciclo;
- apoio à previsão de produção.

**Saída:** métricas derivadas de eventos/pedidos reconciliam com o banco transacional.

## V4.10 — Agente ampliado + hardening

Ferramentas-alvo:
- `consultar_cardapio`;
- `criar_pedido`;
- `consultar_pedido`;
- `alterar_pedido`;
- `cancelar_pedido`;
- `consultar_estoque`;
- `consultar_cliente`;
- `repetir_pedido`.

Hardening:
- permissões por ação;
- idempotência;
- rate limit;
- observabilidade;
- recuperação de falhas;
- backups;
- testes E2E;
- revisão de funções `SECURITY DEFINER`;
- índices e performance.

**Saída:** agente executa somente ações permitidas e toda mutação relevante produz evidência.

## Visão posterior

Somente depois das fases acima:
- previsão de demanda;
- compras/fornecedores;
- multiunidade;
- programa de fidelidade;
- campanhas personalizadas;
- integração fiscal/ERP.
