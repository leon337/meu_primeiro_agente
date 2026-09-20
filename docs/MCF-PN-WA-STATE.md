# PÃO NOSSO — estado operacional persistente

MCF project: pao-nosso
Mission: MCF-20260920-PAO-NOSSO-PRODUCTION-001
Observed: 2026-09-20T06:19:47-03:00

## Linhagem operacional

A base operacional reconciliada é:

feat/pn-wa-audit-persistence@1cb59e3cf99a420357ffa9d0fa7476ef8cbacee2

O main atual não contém todo o módulo PÃO NOSSO; portanto, retomadas não devem
assumir main como estado funcional desta frente até reconciliação/merge explícito.

## Arquitetura funcional preservada

Meta WhatsApp -> /api/whatsapp/webhook -> BakeryChatService -> Gemini -> Supabase -> resposta WhatsApp

O canal WhatsApp usa um assistente dedicado da Pão Nosso e permanece isolado
das ferramentas executivas do AEP.

Capacidades de negócio confirmadas no código:

- bakery_search_catalog;
- bakery_create_order;
- bakery_order_status;
- auditoria WhatsApp/Supabase.

Arquivos centrais:

- app/bakery.py;
- app/server.py;
- app/whatsapp_audit.py;
- app/providers/gemini_provider.py;
- README.md.

## Estado de produção

O usuário confirmou nesta missão que o fluxo WhatsApp está funcionando.
A migração para OCI é uma evolução de runtime, não autorização para desligar
ou substituir o caminho atual antes de validação completa.

## Dependência de infraestrutura

A missão irmã é MCF-20260920-OCI-PAONOSSO-RUNTIME-001.

Estado atual OCI:

- tenancy Oracle ativa em sa-vinhedo-1;
- A1 Flex Always Free configurada para 2 OCPU / 12 GB;
- criação bloqueada por falta de capacidade em AD-1;
- nenhuma VM criada ainda.

## Próxima ação

Manter produção atual. Assim que a VM OCI estiver RUNNING:

1. validar SSH/HTTPS/health;
2. implantar o backend desta linhagem;
3. configurar secrets fora do Git;
4. validar Supabase e Gemini;
5. testar callback Meta em endpoint não destrutivo;
6. executar smoke end-to-end;
7. preparar rollback;
8. somente então solicitar/consumir gate para cutover do webhook de produção.

## Proibições

- Não commitar segredos.
- Não trocar callback Meta por inferência.
- Não desligar o runtime atual antes de OCI validado.
- Não promover main como linhagem PÃO NOSSO sem evidência.
