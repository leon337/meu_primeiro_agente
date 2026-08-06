# Plano — roteamento consistente de navegador

## Objetivo

Garantir que Web Chat e WhatsApp usem o mesmo contrato para:

1. responder perguntas de capacidade com base nas ferramentas realmente registradas;
2. transformar ordens explícitas e inequívocas de navegador em uma missão auditável;
3. manter perguntas conceituais e conversa comum no modelo de IA;
4. informar indisponibilidade real sem inventar execução;
5. preservar segurança, sessão persistente e funções existentes.

## Estratégia

### Camada determinística de intenção

Adicionar um roteador pequeno e independente do provedor, executado por `ChatService` antes de chamar o Gemini. Ele produzirá apenas um dos resultados:

- `capability`: pergunta sobre capacidade de acessar/navegar/pesquisar sites;
- `browser_action`: pedido explícito com destino ou pesquisa suficientemente determinados;
- `fallback`: todo o restante segue para o agente atual.

O roteador não fará classificação geral de linguagem nem tentará substituir a IA. Seu escopo será fechado às intenções exigidas e cobertas por testes.

### Fonte única de verdade para disponibilidade

A capacidade executiva será considerada disponível somente se `aep_submit_mission` estiver presente em `registry.definitions`. O health check também passará a derivar `executive_configured` desse registro, eliminando o falso positivo por mera presença de variáveis.

### Plano de missão previsível

Para pedidos explícitos:

- URL HTTPS informada: `navigate` e, quando solicitado conteúdo/pesquisa, `read_text`;
- Google: destino canônico HTTPS;
- pesquisa: URL HTTPS com consulta codificada e leitura do corpo da página;
- Brave: abrir o aplicativo por `launch_application` quando o pedido for explicitamente sobre o navegador local;
- domínios autorizados derivados das URLs pela implementação já existente;
- `wait_seconds` limitado e resultado sempre associado ao `mission_id` real.

Não haverá execução direta de navegador pela Vercel. O caminho continuará sendo `aep_submit_mission` -> API de controle -> runtime local -> executor auditável.

### Resposta e observabilidade

- Capacidade disponível: explicar que a execução ocorre no computador conectado e gera missão auditável.
- Capacidade indisponível: dizer explicitamente que o runtime executivo não está disponível nesta sessão.
- Missão criada: devolver `mission_id`, estado e evidência/resultado quando existente.
- Falha de autenticação ou runtime: resposta controlada de indisponibilidade, sem vazar erro, URL privada ou token.
- Log estruturado somente com canal/sessão anonimizada, intenção, disponibilidade, rota e `mission_id`; nunca argumentos sensíveis.

## TDD e matriz de testes

Os testes serão escritos e observados falhando antes da implementação.

1. pergunta de capacidade com ferramenta disponível;
2. pergunta de capacidade sem runtime;
3. abrir URL explícita cria missão real no cliente falso;
4. abrir Google cria missão de navegação;
5. abrir Brave cria missão desktop;
6. pesquisa cria navegação e leitura;
7. “explique o que é IA” continua no Gemini e não cria missão;
8. erro de runtime/token retorna indisponibilidade controlada;
9. Web Chat usa o mesmo roteador;
10. WhatsApp usa o mesmo roteador;
11. navegador persistente continua reutilizando o contexto;
12. health só afirma capacidade executiva quando a ferramenta está exposta.

## Validação por fases

1. suíte unitária focada em roteamento;
2. suíte completa `python3 -m pytest -q`;
3. `systemd-analyze verify systemd/*.service`;
4. health local;
5. runtime real com sites públicos sem login: `example.com`, `google.com` e `wikipedia.org`;
6. Preview da Vercel, sem promoção;
7. Web Chat na Preview;
8. WhatsApp em fluxo controlado;
9. inspeção de diff, staged files e varredura de segredos;
10. commit, push e PR sem merge.

## Rollback planejado

O roteador será isolado da lógica do executor. Em caso de regressão, a branch/PR pode ser revertida integralmente sem alterar dados persistentes. Não serão feitas migrações de banco nem mudanças destrutivas.
