# ADR-0005: Money is decimal, rounded to minor units, half away from zero

- Status: Accepted
- Date: 2025-10-27
- Last amended: 2026-09-30 (known deviations recorded)
- Deciders: @kestrel/pricing-team, @kestrel/booking-team, @kestrel/web-team, @kestrel/architecture-guild

## Context

Freight pricing produces many small adjustments: per-kg rates, fuel surcharge, zone
supplements, currency conversion. In kestrel-core amounts were `double`, and customers
saw totals that differed by a cent between the quote screen and the invoice. Finance
reconciled these by hand every month (about 40 invoices per month in Q2 2025).

Two separate questions needed a single answer for all services:

1. What numeric representation do we use?
2. When a value falls exactly halfway between two minor units (for example 10.125 to two
   decimals), which way does it round?

.NET's `Math.Round(decimal, int)` defaults to banker's rounding (`MidpointRounding.ToEven`),
which gives 10.12. Our carrier contracts, and the invoicing system, round halves away from
zero, giving 10.13. The difference is rare per line but systematic across volume.

## Decision

1. **Representation.** Money is never binary floating point. Pricing computes with
   `decimal`. Amounts are persisted and compared in integer **minor units** (cents for
   EUR/USD, whole yen for JPY) together with an ISO 4217 currency code. The currency's
   exponent comes from a single table in pricing.
2. **Rounding rule.** All rounding is `MidpointRounding.AwayFromZero`.
3. **One helper.** In pricing, every rounding goes through `Money.Round`, which wraps
   `Math.Round(value, exponent, MidpointRounding.AwayFromZero)`. Direct calls to
   `Math.Round` on monetary values are not allowed in code review.
4. **Clients do not compute money.** The gateway and web display amounts returned by
   pricing. Where the UI must derive a figure (for example a running total of two quotes),
   it works on integer minor units or a decimal library, never `number` arithmetic.

## Consequences

- Positive: quote screen, invoice and carrier statement agree to the minor unit.
- Positive: one grep (`Money.Round` vs `Math.Round`) audits compliance.
- Negative: a contributor who does not know the rule will reach for the default
  `Math.Round`, which silently differs only on exact halves. Tests must therefore include
  half-way fixtures such as 10.125 and 0.005.
- Known deviations, recorded 2026-09-30 and tracked in PRC-233: the fuel-surcharge step
  in `QuoteCalculator.ApplyFuelSurcharge` still calls `Math.Round(value, 2)` (ToEven), and
  `kestrel-web/src/lib/money.ts` implements `roundMoney` with `Math.round`, which rounds
  halves toward positive infinity and works on binary floats. Both predate or ignore this
  ADR. Fixing them is in scope for PRC-233; this ADR is the authority on the target
  behaviour.
