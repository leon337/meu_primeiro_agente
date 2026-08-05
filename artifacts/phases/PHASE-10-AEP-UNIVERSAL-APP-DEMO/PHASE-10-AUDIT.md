# Auditoria independente — Fase 10

## Resultado atualizado

`PASS_WITH_SECRET_ROTATION_REQUIRED`

## Evidências revisadas

- implementação de registro, listagem, abertura e foco de aplicativos;
- ausência de `shell=True` e de comandos arbitrários;
- manutenção de aprovação para ações de alteração em controles;
- contrato `demo_only` persistido na missão e no recibo;
- política negativa para depósito, saque, transferência, credenciais e ordem real;
- CI em Python 3.11 e 3.12;
- deployment Preview da Vercel;
- gate local real no Linux Mint;
- 159 aplicativos registrados descobertos;
- Brave/Hello Agent aberto e focalizado;
- Visual Studio Code aberto e focalizado;
- política demonstrativa retornando `FINANCIAL_DEMO_CONFIRMATION`;
- efeito financeiro real bloqueado com `REAL_FINANCIAL_EFFECT_BLOCKED`.

## Achados

### A-01 — Escopo de “qualquer aplicativo”

**Severidade:** baixa.

O acesso universal limita-se a aplicativos gráficos registrados em arquivos `.desktop`. Isso evita transformar texto do usuário em comando de sistema, mas aplicativos portáteis sem registro precisarão de cadastro prévio.

### A-02 — Acessibilidade variável

**Severidade:** baixa.

AT-SPI não garante que todos os aplicativos exponham controles internos. Abertura e foco possuem fallback de janela, porém clique, leitura e preenchimento por nome dependem da árvore de acessibilidade do aplicativo.

### A-03 — Ambiente demonstrativo

**Severidade:** controlada.

O gate local provou que uma ação financeira demonstrativa é permitida apenas com confirmação humana e que efeitos financeiros reais continuam bloqueados. Ainda é necessário confirmar visualmente que a conta exibida é demonstrativa antes de aprovar qualquer etapa financeira de teste.

### A-04 — Segredos previamente expostos

**Severidade:** alta operacional.

Capturas anteriores exibiram partes de chaves e credenciais. A implementação desta fase não adicionou segredos ao repositório, mas a rotação dos valores expostos continua obrigatória antes de merge ou uso contínuo.

## Gates concluídos

1. gate local no Linux Mint: **PASS**;
2. listagem de aplicativos registrados: **PASS — 159 encontrados**;
3. abertura e foco do Brave/Hello Agent: **PASS**;
4. abertura e foco do Visual Studio Code: **PASS**;
5. confirmação obrigatória para teste financeiro demonstrativo: **PASS**;
6. bloqueio de efeito financeiro real: **PASS**;
7. CI Python 3.11 e 3.12: **PASS**;
8. Preview Vercel: **PASS**.

## Bloqueio remanescente

- rotacionar os segredos previamente expostos;
- repetir o health check após a rotação;
- obter decisão operacional de Léo;
- obter autorização humana explícita antes de merge.

## Conclusão

A Fase 10 atingiu o objetivo técnico de acesso a aplicativos gráficos registrados e de modo financeiro demonstrativo controlado. O código e os gates técnicos receberam `PASS`. O PR deve permanecer Draft e sem merge enquanto a rotação de segredos e os gates finais não forem concluídos.
