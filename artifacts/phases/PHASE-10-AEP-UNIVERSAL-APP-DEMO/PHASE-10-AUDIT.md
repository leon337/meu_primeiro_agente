# Auditoria independente — Fase 10

## Resultado provisório

`PASS_WITH_LOCAL_GATE_PENDING`

## Evidências revisadas

- implementação de registro e lançamento de aplicativos;
- ausência de `shell=True` e de comandos arbitrários;
- manutenção de aprovação para ações de alteração em controles;
- contrato `demo_only` persistido na missão e no recibo;
- política negativa para depósito, saque, transferência, credenciais e ordem real;
- CI em Python 3.11 e 3.12;
- deployment Preview da Vercel.

## Achados

### A-01 — Escopo de “qualquer aplicativo”

**Severidade:** baixa.

O acesso universal limita-se a aplicativos gráficos registrados em arquivos `.desktop`. Isso evita transformar texto do usuário em comando de sistema, mas aplicativos portáteis sem registro precisarão de cadastro prévio.

### A-02 — Acessibilidade variável

**Severidade:** baixa.

AT-SPI não garante que todos os aplicativos exponham controles internos. Abertura e foco possuem fallback de janela, porém clique, leitura e preenchimento por nome dependem da árvore de acessibilidade do aplicativo.

### A-03 — Ambiente demonstrativo precisa ser confirmado visualmente

**Severidade:** média controlada.

As flags impedem efeitos financeiros declarados, mas a interface remota ainda precisa apresentar evidência inequívoca de conta demonstrativa antes de uma etapa financeira ser aprovada. A confirmação humana obrigatória foi preservada para esse gate.

### A-04 — Segredos previamente expostos

**Severidade:** alta fora do código desta fase.

Capturas anteriores exibiram partes de chaves e credenciais. A rotação de segredos continua obrigatória antes de considerar o sistema pronto para uso contínuo.

## Bloqueios para merge

1. executar gate local no Linux Mint;
2. provar listagem, abertura e foco de pelo menos Brave e Visual Studio Code;
3. provar que uma ação demonstrativa solicita aprovação;
4. provar que depósito ou ordem real retorna bloqueio;
5. rotacionar segredos expostos.

## Conclusão

A arquitetura é adequada para teste controlado. Não há autorização para merge ou produção enquanto os gates locais e a rotação de segredos estiverem pendentes.
