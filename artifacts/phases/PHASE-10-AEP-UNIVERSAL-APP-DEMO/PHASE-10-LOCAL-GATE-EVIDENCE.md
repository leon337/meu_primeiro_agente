# Evidência do gate local — Fase 10

## Origem

- Operador: Leandro
- Ambiente: Linux Mint local
- Data informada no ciclo: 2026-08-05
- Branch: `feat/aep-universal-app-demo-mode`
- Script: `scripts/validate_aep_universal_app_demo.py --real`

## Serviços

```text
hello-agent-bridge.service: active
hello-agent-executive.service: active
```

## Resultado do gate

```json
{
  "gate": "AEP_UNIVERSAL_APP_DEMO_LOCAL",
  "status": "COMPLETED",
  "result": "PASS",
  "registered_application_count": 159
}
```

## Aplicativos comprovados

### Brave / Hello Agent

```json
{
  "query": "Brave",
  "name": "Hello Agent",
  "desktop_id": "brave-kibgpaeblmfaafcaodnokdkfblbamglo-Default",
  "launched": true,
  "focused": true
}
```

### Visual Studio Code

```json
{
  "query": "Visual Studio Code",
  "name": "Visual Studio Code",
  "desktop_id": "code",
  "launched": true,
  "focused": true
}
```

## Política financeira demonstrativa comprovada

```json
{
  "configured": true,
  "allowed": true,
  "requires_approval": true,
  "code": "FINANCIAL_DEMO_CONFIRMATION",
  "real_effect_blocked": true,
  "real_effect_code": "REAL_FINANCIAL_EFFECT_BLOCKED"
}
```

## Veredito técnico

`PASS`

O gate local comprovou descoberta de 159 aplicativos registrados, abertura e foco real de Brave/Hello Agent e Visual Studio Code, exigência de aprovação para ação financeira demonstrativa e bloqueio de efeito financeiro real.

## Limite ainda aberto

A rotação dos segredos previamente expostos em capturas continua obrigatória antes de merge ou uso contínuo.
