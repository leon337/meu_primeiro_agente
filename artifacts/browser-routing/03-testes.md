# Testes — consistência do roteamento de navegador

Data: 2026-08-06
Branch: `fix/aep-browser-routing-consistency`

## Ciclo TDD

O arquivo `tests/test_browser_intent_routing.py` foi criado antes da implementação.

Primeiro resultado observado:

```text
10 failed, 1 passed
```

As falhas cobriam resposta de capacidade, Google, Brave, URL explícita, pesquisa, indisponibilidade, erro de token/runtime, Web, WhatsApp e health falso-positivo. A única passagem inicial era a pergunta conceitual que já permanecia no fluxo normal da IA.

Depois da primeira implementação, a suíte focada formada por roteamento, ferramentas executivas, canais e sessão persistente retornou:

```text
20 passed
```

## Regressões descobertas pelo runtime real

O primeiro gate real encontrou dois casos ausentes dos mocks:

1. o texto de Playwright aparece em `evidence[].data.outputs[].text`;
2. a grafia acentuada `Wikipédia` não era removida da expressão de pesquisa.

Foram adicionados testes específicos e ambos falharam antes da segunda correção:

```text
2 failed
```

Após corrigir o parser de recibo e a expressão regular:

```text
2 passed
```

## Suíte final local

Comando:

```bash
python3 -m pytest -q
```

Resultado:

```text
88 passed
```

Validações adicionais:

```bash
systemd-analyze verify systemd/*.service
git diff --check
```

Ambas terminaram com código zero e sem saída de erro.

## Matriz coberta

| Caso | Resultado |
|---|---|
| pergunta de capacidade com runtime | passa; resposta fundamentada no registro |
| pergunta de capacidade sem runtime | passa; informa indisponibilidade |
| URL HTTPS explícita | passa; cria `navigate` e leitura quando solicitada |
| Google | passa; usa URL canônica |
| Brave | passa; usa ação desktop declarativa |
| pesquisa Wikipédia | passa; consulta limpa e `read_text` |
| pergunta conceitual sobre IA | passa; permanece no Gemini |
| token/runtime inválido | passa; erro controlado sem segredo |
| endpoint Web | passa; usa o mesmo roteador |
| resposta WhatsApp | passa; usa o mesmo roteador |
| sessão persistente | passa; um contexto entre missões |
| health em registro legado | passa; não anuncia capacidade inexistente |
| recibo no formato real | passa; devolve `Example Domain` |

## Gate de Preview posterior à suíte

Depois da publicação da branch, o Preview protegido passou no health, na pergunta de capacidade, na missão Web real para `example.com` e na pergunta conceitual. O teste WhatsApp real no Preview permanece pendente e não foi tratado como aprovado pela cobertura automatizada.
