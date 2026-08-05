# PHASE-08 — Plano de correção da rastreabilidade MCF

```yaml
mission_contract:
  mission_id: MCF-AEP-001
  parent_mission_id: null
  phase_id: PHASE-08-MCF-TRACEABILITY-REPAIR
  objective: Corrigir a não conformidade metodológica, materializar o PRF e registrar o gate local do Agente Executivo Pessoal.
  expected_outcome: Pacote de rastreabilidade completo, auditável e ligado ao PR 11.
  scope:
    - registrar a falha metodológica
    - preservar a evidência do gate local
    - criar plano, relatório, validações, smoke, checkpoint, decisões, trace e manifesto
    - auditar conformidade ESEV e PRF
    - emitir gate operacional
  out_of_scope:
    - alterar código funcional já submetido ao gate local
    - instalar systemd
    - ativar navegador ou desktop em modo irrestrito
    - fazer merge do PR
    - executar publicação externa
  source_of_truth:
    - MCF Project Operating Instructions v1.0.0
    - MCF-DEC-051
    - PR leon337/meu_primeiro_agente#11
    - commit validado 3e4dfd5f9a770968d3a675bfde1e4a4a71b3b369
    - captura local sha256:61a1db6cbf124a280bc434c62254e9d9fe6572b32f942acad7b33ed5aaeda909
  acceptance_criteria:
    - não conformidade descrita sem ocultação
    - cada agente selecionado produz artefato ou validação verificável
    - passagens registradas cronologicamente
    - gate local PASS preservado com evidência
    - PRF mínimo completo
    - auditoria independente emitida
    - decisão de Léo registrada
    - checkpoint permite retomada sem reconstrução inventada
  authorizations:
    - SCOPED_WRITE no branch integration/aep-7-phases-2.1.3
    - leitura do repositório MCF
    - leitura do PR 11 e seus checks
  prohibitions:
    - merge
    - deploy de produção
    - instalação de serviços
    - exposição de credenciais
    - atribuição de ação sem evidência
  risk_class: B
  cycle: 1
  selected_skills:
    - MCF-START-MISSION
    - MCF-IMPLEMENT-CHANGE
    - MCF-RUN-TESTS
  selected_agents:
    - Mestre
    - Miriam
    - Carmem
    - Renato
    - Augusto
    - Gabriel
    - Emily
    - Leo
  decision_authority: Leo
```

## Justificativa da equipe

- **Mestre:** contrato, ordem cronológica e fechamento.
- **Miriam:** fontes, precedência e checkpoint recuperável.
- **Carmem:** documentação do PRF.
- **Renato:** validação dos checks e evidência local.
- **Augusto:** mission trace e verificação das passagens.
- **Gabriel:** vínculo com branch, commits, PR e manifesto.
- **Emily:** auditoria independente.
- **Léo:** gate operacional.

Os demais agentes não foram selecionados porque esta fase é documental e de conformidade; não exige nova arquitetura, backend, frontend, banco, IA, design, acessibilidade, mobile ou infraestrutura de produção.

## Ordem inicial

```text
Mestre
→ Miriam
→ Carmem
→ Renato
→ Augusto
→ Gabriel
→ Emily
→ Léo
→ Mestre
```

Retornos são permitidos quando a validação ou auditoria encontrar lacuna.

## Estratégia de validação

1. confirmar o estado do PR e do commit validado;
2. registrar a saída local fornecida por Leandro;
3. confirmar checks remotos do commit validado;
4. validar completude do PRF;
5. gerar manifesto SHA-256;
6. auditar ESEV, artefatos, handoffs e estado final.
