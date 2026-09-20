# PHASE-PN-ORDER-IDENTITY-001 — Report

## Incident
The storefront persisted the reported order correctly, but the WhatsApp lookup returned `found:false`.

## Root cause
The production lookup compared the rightmost 11 digits of raw phone strings. A Meta representation using country code + a 10-digit Brazilian national mobile number was therefore not equivalent to the storefront representation using the national mobile number with the ninth digit.

The audit ledger proved that:
- the order existed in `public.orders`;
- WhatsApp called `bakery_order_status` with the correct order code;
- the RPC returned `found:false`;
- the failure was phone identity normalization, not an invented order code or missing persistence.

## Change
Migration source:
`supabase/migrations/20260920124500_fix_br_phone_identity.sql`

Live Supabase migration:
`20260920124044_fix_br_phone_identity`

The migration:
- adds `public.normalize_br_phone(text)`;
- makes `customer_order_status` compare canonical phone identities;
- makes `create_order` store future customer phones canonically;
- does not rewrite historical orders.

## Result
Post-migration validation:
- equivalent formats: PASS;
- valid order + equivalent WhatsApp identity: 1 row;
- valid order + unrelated identity: 0 rows;
- reverse compatibility with an earlier order representation: 1 row.

## Findings outside scope
Supabase advisors still report pre-existing warnings for executable SECURITY DEFINER RPCs and unindexed foreign keys. No new warning was attributed to `normalize_br_phone`. These findings are recorded for a separate hardening mission.
