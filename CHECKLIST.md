# Pão Nosso V4 — Checklist de Implementação

> Atualizar este arquivo em toda implantação.  
> `[x]` exige evidência verificável; intenção ou código não testado permanece `[ ]`.

## Estado global

- [x] Repositório operacional identificado: `leon337/meu_primeiro_agente`
- [x] Missão MCF criada: `MCF-PAO-NOSSO-V4-001`
- [x] Issue de produto criada: #19
- [x] Issue MCF criada: `multiagent-collaboration-framework#375`
- [x] Branch de missão criada: `mission/pao-nosso-v4-001`
- [x] Roadmap versionado
- [x] Issues por fase criadas (#20–#30)
- [x] Storefront público verificado: `https://paonosso-v3.vercel.app`
- [x] Backend/AEP-WhatsApp público identificado: `https://meu-primeiro-agente-indol.vercel.app`
- [x] Banco Supabase identificado: projeto `paonosso-v3`, região `sa-east-1`
- [ ] Código-fonte do storefront `paonosso-v3.vercel.app` reconciliado com Git canônico

## V4.0 — Fundação (#20)

- [x] Criar missão e contrato MCF
- [x] Criar roadmap
- [x] Criar checklist
- [x] Criar issues de implantação
- [x] Criar arquitetura documentada
- [x] Criar mapa de serviços/hosting
- [x] Criar runbook operacional
- [x] Atualizar Project Capsule
- [x] Atualizar README com funcionamento e hosting
- [ ] Localizar/exportar a fonte exata do storefront V3
- [ ] Versionar o storefront no repositório canônico
- [ ] Definir pipeline de deploy reproduzível do storefront
- [ ] Executar smoke reproduzível site → banco → WhatsApp
- [ ] Fechar PRF V4.0 e marcar issue #20 concluída

## V4.1 — Painel operacional (#21)

- [ ] Definir wireframe e papéis de acesso
- [ ] API/listagem de pedidos
- [ ] Realtime de novos pedidos
- [ ] Colunas por status
- [ ] Alteração segura de status
- [ ] Filtros
- [ ] Tempo de espera
- [ ] Auditoria de mudanças
- [ ] Responsividade
- [ ] Testes + smoke
- [ ] Documentação e checkpoint

## V4.2 — Status + WhatsApp (#22)

- [ ] Evento canônico de status
- [ ] Worker/dispatcher de notificações
- [ ] Idempotência por evento
- [ ] Templates de mensagens
- [ ] “Onde está meu pedido?”
- [ ] Estado de envio/erro
- [ ] Retry seguro
- [ ] Testes + smoke
- [ ] Documentação e checkpoint

## V4.3 — Clientes (#23)

- [ ] Tabela/entidade `customers`
- [ ] Telefone canônico único
- [ ] Endereços
- [ ] Histórico
- [ ] Preferências explícitas
- [ ] Repetir último pedido
- [ ] Política de acesso/retenção
- [ ] Migração/backfill seguro
- [ ] Testes de isolamento
- [ ] Documentação e checkpoint

## V4.4 — Cardápio admin (#24)

- [ ] Tela administrativa
- [ ] Criar/editar/desativar produto
- [ ] Preço e unidade
- [ ] Categoria
- [ ] Foto
- [ ] Disponibilidade
- [ ] Destaque/promoção
- [ ] Auditoria
- [ ] Testes + smoke
- [ ] Documentação e checkpoint

## V4.5 — Produção (#25)

- [ ] Modelo de fila
- [ ] Agregação de quantidades
- [ ] Prioridade/horário
- [ ] Visão cozinha
- [ ] Marcar preparado/pronto
- [ ] Sincronizar status do pedido
- [ ] Testes + smoke
- [ ] Documentação e checkpoint

## V4.6 — Estoque (#26)

- [ ] Modelo de estoque
- [ ] Entrada/saída/ajuste
- [ ] Reserva por pedido
- [ ] Baixa
- [ ] Produto esgotado
- [ ] Bloqueio de oversell
- [ ] Alertas de mínimo
- [ ] Auditoria
- [ ] Testes concorrentes
- [ ] Documentação e checkpoint

## V4.7 — Pix (#27)

- [ ] Escolher integração autorizada
- [ ] Criar cobrança ligada ao pedido
- [ ] QR Code/copia-e-cola
- [ ] Webhook validado
- [ ] Idempotência
- [ ] Estados de pagamento
- [ ] Conciliação
- [ ] Expiração/cancelamento
- [ ] Testes sandbox
- [ ] Gate de produção
- [ ] Documentação e checkpoint

## V4.8 — Entrega (#28)

- [ ] Endereço estruturado
- [ ] Área atendida
- [ ] Taxa
- [ ] Previsão
- [ ] Atribuir entregador
- [ ] Saiu para entrega
- [ ] Entregue
- [ ] Auditoria
- [ ] Testes + smoke
- [ ] Documentação e checkpoint

## V4.9 — Analytics (#29)

- [ ] Definir métricas canônicas
- [ ] Faturamento
- [ ] Ticket médio
- [ ] Produtos mais vendidos
- [ ] Horários de pico
- [ ] Recorrência
- [ ] Conversão site × WhatsApp
- [ ] Tempo de ciclo
- [ ] Cancelamentos
- [ ] Exportação/relatório
- [ ] Reconciliação com pedidos
- [ ] Documentação e checkpoint

## V4.10 — Agente + hardening (#30)

- [ ] `alterar_pedido`
- [ ] `cancelar_pedido`
- [ ] `consultar_estoque`
- [ ] `consultar_cliente`
- [ ] `repetir_pedido`
- [ ] Permissões por ferramenta
- [ ] Confirmação em mutações sensíveis
- [ ] Idempotência
- [ ] Rate limit
- [ ] Observabilidade
- [ ] Backup/restore
- [ ] Revisar `SECURITY DEFINER`
- [ ] Criar índices necessários
- [ ] Testes E2E completos
- [ ] Auditoria independente
- [ ] Runbook final
