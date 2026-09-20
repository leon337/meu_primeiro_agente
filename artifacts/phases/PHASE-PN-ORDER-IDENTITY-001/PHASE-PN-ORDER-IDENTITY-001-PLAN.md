# PHASE-PN-ORDER-IDENTITY-001 — Plano

Mission: MCF-20260920-PAO-NOSSO-ORDER-IDENTITY-001
Issue: #17
Risk class: C
Coordinator: MESTRE
Human authority: LEANDRO
Decision authority: LÉO

## Objective
Restore reliable order lookup between the Pão Nosso storefront and WhatsApp when the same Brazilian mobile number is represented differently by the form and Meta.

## Scope
- confirm the incident from live audit evidence;
- preserve lookup authorization as order code + equivalent customer phone;
- canonicalize Brazilian phone identity in the database;
- keep historical orders intact;
- validate positive, negative and backward-compatible cases;
- version the production migration and create a PRF.

## Out of scope
- changing Meta credentials or webhook callback;
- changing storefront UX;
- merging unrelated Supabase security/performance debt;
- rewriting historical order rows.

## Sources of truth
- live Supabase project `paonosso-v3`;
- branch `mission/pao-nosso-context-20260920`;
- `app/bakery.py`;
- `app/server.py`;
- `docs/MCF-PN-WA-STATE.md`;
- MCF operational protocol v1.1.

## Selected agents
MESTRE, Patrícia, Manoel, Eduardo, Beatriz, Ricardo, Renato, Augusto, Carmem, Emily, Gabriel, Júlia and LÉO.

## Acceptance criteria
1. Equivalent Brazilian phone representations normalize to one identity.
2. A valid order queried with the equivalent WhatsApp identity returns exactly one row.
3. The same order queried with an unrelated phone returns zero rows.
4. Earlier order representations remain queryable.
5. Future orders are stored using the canonical phone representation.
6. No customer phone, secret or credential is committed.

## Rollback
Restore the previous definitions of `create_order` and `customer_order_status` from the pre-migration catalog snapshot and drop `normalize_br_phone(text)` only after verifying that no later migration depends on it.
