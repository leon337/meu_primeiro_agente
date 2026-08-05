# MCF-AEP-001 — Agente Executivo Pessoal

**Autoridade humana final:** Leandro  
**Coordenação:** Mestre  
**Gate operacional delegado:** Léo  
**Repositório:** `leon337/meu_primeiro_agente`  
**Branch:** `feat/aep-phase-1-mission-runtime`  
**Estado:** EM EXECUÇÃO — FASE 1

## Objetivo

Transformar o Hello Agent em um Agente Executivo Pessoal integrado ao MCF, capaz de receber missões, operar inicialmente no navegador, executar tarefas autorizadas em nome de Leandro, produzir evidências verificáveis e devolver o resultado ao agente MCF solicitante.

O objetivo não é conceder acesso irrestrito ao computador. A autonomia será ampliada por níveis, com políticas explícitas, limites técnicos e gates humanos para ações sensíveis.

## Resultado esperado

O agente deverá:

1. receber uma missão estruturada do MCF ou de Leandro;
2. decompor o objetivo em etapas observáveis;
3. classificar cada ação por risco;
4. executar somente ações compatíveis com sua política;
5. pausar quando encontrar MFA, CAPTCHA, pagamento, alteração de senha ou decisão reservada;
6. registrar ações, evidências, erros e aprovações;
7. retomar tarefas interrompidas sem perder o estado;
8. devolver o resultado para a missão de origem.

## Primeira capacidade operacional

A primeira entrega será um **Operador Web Supervisionado do MCF**.

Sites-alvo iniciais:

- GitHub;
- Vercel;
- Render;
- Neon;
- Cloudflare;
- Linear;
- Supabase.

Capacidades iniciais:

- abrir e navegar em sites autorizados;
- reutilizar sessão autenticada local;
- localizar dados e estados;
- preencher formulários;
- preparar ações externas;
- concluir ações de baixo risco previamente autorizadas;
- capturar evidências antes e depois;
- devolver resultado estruturado ao MCF.

## Níveis de autonomia

### Nível 1 — Observação

Pode consultar, navegar, baixar logs e capturar evidências.

### Nível 2 — Preparação

Pode preencher formulários e deixar operações prontas, sem confirmar a ação final.

### Nível 3 — Execução autorizada

Pode concluir ações reversíveis e previamente permitidas, como iniciar deploy, criar recurso gratuito autorizado ou atualizar configuração não sensível.

### Nível 4 — Gate imediato

Deve pedir aprovação antes de publicar, enviar mensagens a terceiros, conceder acesso, instalar programas ou executar alteração difícil de reverter.

### Nível 5 — Exclusivamente humano

Não pode executar sozinho pagamentos, compras, contratos, operações bancárias, troca de senha, alteração de MFA, exclusão definitiva, cadastro de cartão, recuperação de conta ou fornecimento de documento de identidade.

## Invariantes de segurança

- preservar o `ToolRegistry` fechado;
- não criar ferramenta genérica `run_command`;
- não fornecer shell irrestrito ao modelo;
- não enviar senha, token, cookie ou segredo ao modelo;
- credenciais devem ser preenchidas por um corretor local;
- MFA e CAPTCHA exigem intervenção humana;
- toda ação externa deve possuir identificação da missão;
- toda mudança relevante deve gerar recibo e evidência;
- deve existir cancelamento imediato e botão de emergência;
- o agente não pode ampliar suas próprias permissões;
- nenhum merge em `main` ocorre sem validação, auditoria e gate de Léo.

## Equipe selecionada

- **Mestre:** coordenação, sequência e retorno à missão-pai;
- **Leonardo:** requisitos, histórias e critérios de aceitação;
- **Sofia:** arquitetura do runtime e integração MCF;
- **Rafael:** implementação do núcleo;
- **Ricardo:** modelo de ameaças e motor de políticas;
- **Renato:** testes unitários, integração e regressão;
- **Bruno:** runtime local, empacotamento e observabilidade;
- **Gabriel:** branch, commits, CI e pull request;
- **Carmem:** documentação operacional;
- **Augusto:** eventos, rastreabilidade e métricas multiagente;
- **Miriam:** estado persistente e memória institucional;
- **Emily:** auditoria independente;
- **Léo:** decisão operacional e gate de integração.

A participação é dinâmica. Agentes não necessários em uma fase não serão convocados apenas para compor a resposta.

## Fases

1. Runtime de missões e contratos.
2. Motor de políticas e níveis de autonomia.
3. Operador web supervisionado.
4. Integração formal com o MCF.
5. Comandos e respostas por voz.
6. Controle de aplicativos Linux por acessibilidade.
7. Autonomia contínua, memória e recuperação.

## Critérios gerais de conclusão

- testes automatizados aprovados;
- nenhuma regressão nas quatro ferramentas atuais;
- nenhum segredo no Git ou nos logs;
- missão persistida com estado e eventos;
- ações bloqueadas por política não podem ser contornadas pelo modelo;
- execução interrompida pode ser retomada;
- evidências permitem reconstruir o que aconteceu;
- auditoria independente concluída;
- gate de Léo aprovado;
- Leandro permanece autoridade humana final.
