# Mission trace — MCF-20260920-PAO-NOSSO-ORDER-IDENTITY-001

## MESTRE — contract
Input: user-authorized Pão Nosso production incident.
Action: consulted current MCF protocol and current Pão Nosso Git lineage.
Evidence: MCF protocol v1.1; mission branch head; live Supabase project.
Handoff: MESTRE → Patrícia.

## Patrícia — incident diagnosis
Action: correlated persisted order, WhatsApp ledger tool call and RPC result.
Evidence: order persisted; `bakery_order_status` called; pre-fix result `found:false`.
Decision: persistence was healthy; identity matching failed.
Handoff: Patrícia → Manoel.

## Manoel — database diagnosis
Action: inspected live `create_order` and `customer_order_status` definitions.
Evidence: lookup used `right(...,11)` against raw digits.
Decision: canonicalization required at database boundary.
Handoff: Manoel → Ricardo.

## Ricardo — security boundary
Action: reviewed access invariant before mutation.
Decision: keep order-code + phone matching; do not weaken to code-only lookup.
Handoff: Ricardo → Gabriel/Manoel.

## Gabriel — controlled branch
Action: created `fix/pn-order-phone-identity-20260920` from the mission branch.
Evidence: branch created from current mission checkpoint.
Handoff: Gabriel → Manoel.

## Manoel — implementation
Action: versioned canonicalization migration and applied it through Supabase migrations.
Evidence: Git commit `9366d2ae...`; live migration `20260920124044_fix_br_phone_identity`.
Handoff: Manoel → Renato.

## Renato — validation
Action: repeated failed lookup and isolation cases after migration.
Evidence: equivalent=true; correct=1; unrelated=0; reverse-compatible=1.
Handoff: Renato → Ricardo.

## Ricardo — post-change review
Action: ran Supabase security/performance advisors.
Evidence: only pre-existing SECURITY DEFINER and FK-index findings recorded; no new normalization-specific warning.
Handoff: Ricardo → Carmem/Augusto.

## Carmem/Augusto — traceability
Action: generated Class C PRF and continuity checkpoint.
Handoff: Carmem/Augusto → Emily/Gabriel.

## Pending
- independent audit;
- PR linkage;
- LÉO final gate.
