# MCF-AEP-001 — Evidência de CI remoto

**Data:** 4 de agosto de 2026  
**Workflow:** `AEP CI`  
**Run:** `30941747632`  
**HEAD:** `1b15865e73ec78b3ed00dea5bb44e418092d38dc`

## Primeiro ciclo

O primeiro run encontrou uma regressão documental no teste da PWA: a interface havia sido renomeada para `Agente Executivo Pessoal`, enquanto o teste ainda exigia `Hello Agent`.

A expectativa foi corrigida para validar a nova identidade e o idioma `pt-BR`.

## Segundo ciclo

```yaml
python_3_11:
  install: PASS
  compileall: PASS
  pytest: PASS
python_3_12:
  install: PASS
  compileall: PASS
  pytest: PASS
workflow_conclusion: SUCCESS
```

Nenhum merge foi executado. A ativação real de navegador, desktop e daemon continua condicionada aos smokes locais de baixo risco.
