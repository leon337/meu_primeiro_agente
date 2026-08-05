# MCF-AEP-001 — Fase 1: Runtime de Missões

**Estado:** INICIADA  
**Branch:** `feat/aep-phase-1-mission-runtime`

## Objetivo da fase

Criar a fundação persistente e auditável que permitirá ao agente trabalhar por objetivo, executar etapas, pausar em gates, recuperar falhas e retornar o resultado ao MCF.

A Fase 1 não adicionará controle irrestrito do navegador ou do desktop. Ela prepara o núcleo que controlará essas capacidades nas fases seguintes.

## Escopo aprovado

### 1. Contrato de missão

Cada missão deve possuir:

- `mission_id`;
- origem e agente solicitante;
- objetivo;
- contexto mínimo;
- sites e capacidades permitidos;
- ações proibidas;
- nível máximo de autonomia;
- critérios de conclusão;
- política de evidências;
- destino do retorno;
- estado e versão.

### 2. Máquina de estados

Estados iniciais:

```text
CREATED
→ PLANNING
→ READY
→ RUNNING
→ WAITING_HUMAN
→ BLOCKED
→ RECOVERING
→ COMPLETED
→ FAILED
→ CANCELLED
```

Transições inválidas devem ser rejeitadas.

### 3. Etapas e checkpoints

Cada etapa deve registrar:

- ordem causal;
- executor;
- ação planejada;
- estado;
- tentativas;
- evidências;
- erro sanitizado;
- próxima ação;
- gate necessário;
- versão otimista.

### 4. Eventos e auditoria

Eventos mínimos:

- missão criada;
- plano aprovado;
- etapa iniciada;
- ferramenta solicitada;
- política consultada;
- ação autorizada ou bloqueada;
- evidência registrada;
- intervenção humana solicitada;
- tarefa retomada;
- tarefa concluída;
- retorno enviado ao MCF.

### 5. Persistência

A primeira implementação poderá utilizar SQLite local para o MVP, desde que:

- a camada de persistência tenha contrato substituível;
- migrações sejam versionadas;
- escrita seja transacional;
- o estado sobreviva ao reinício;
- nenhuma credencial seja armazenada;
- seja possível migrar depois para PostgreSQL.

### 6. Cancelamento e emergência

Toda missão em execução deve aceitar:

- cancelamento normal;
- pausa imediata;
- parada de emergência;
- expiração por tempo;
- bloqueio por política.

A parada de emergência deve impedir novas ações externas, preservando estado e evidências já produzidas.

## Estrutura inicial prevista

```text
app/
  missions/
    __init__.py
    models.py
    service.py
    state_machine.py
    repository.py
    events.py
  policies/
    __init__.py
    models.py
    engine.py
    default_policy.yaml
  audit/
    __init__.py
    ledger.py
    receipts.py
```

## Trabalho por agente

### Leonardo

- fechar histórias de usuário;
- definir critérios de aceitação e cenários de bloqueio.

### Sofia

- definir contratos, dependências e fronteiras entre chat, missão, política, executor e auditoria.

### Ricardo

- definir classificação de risco e decisões que nunca podem depender apenas do modelo.

### Rafael

- implementar modelos, máquina de estados, repositório e serviço de missão.

### Miriam

- definir retenção, recuperação e separação entre memória de conversa e memória operacional.

### Augusto

- definir eventos, correlação, métricas e sequência causal.

### Renato

- testar transições, concorrência, retomada, idempotência, cancelamento e regressão.

### Emily

- executar auditoria independente antes do gate.

### Léo

- autorizar ou bloquear a integração da fase.

## Critérios de aceitação da Fase 1

1. Criar uma missão válida e persistir seu estado.
2. Rejeitar contrato incompleto ou política inválida.
3. Impedir transição de estado não autorizada.
4. Registrar eventos em ordem causal.
5. Retomar missão após reinício do processo.
6. Impedir duas atualizações concorrentes sobre a mesma versão.
7. Pausar uma missão em `WAITING_HUMAN`.
8. Cancelar e bloquear novas ações.
9. Executar parada de emergência.
10. Não armazenar credenciais, cookies ou tokens.
11. Preservar os testes e ferramentas existentes.
12. Produzir documentação e recibo de validação.

## Fora do escopo desta fase

- Playwright;
- controle de mouse e teclado;
- execução de shell;
- leitura ou edição de conteúdo de arquivos;
- armazenamento de senhas;
- captura contínua de tela;
- escuta permanente do microfone;
- pagamentos ou ações jurídicas;
- publicação automática irrestrita.

## Sequência de execução

```text
Leonardo fecha requisitos
→ Sofia fecha arquitetura
→ Ricardo fecha políticas mínimas
→ Rafael implementa o núcleo
→ Miriam e Augusto validam estado e eventos
→ Renato executa testes
→ Emily audita
→ Léo decide o gate
→ Mestre retorna à missão-pai
```
