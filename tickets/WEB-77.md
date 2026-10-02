# WEB-77: Web Shipment type is missing eta_confidence

| Field | Value |
|---|---|
| Status | open |
| Component | web |
| Owner team | @kestrel/web-team |
| Created | 2026-09-19 |
| Closed | |
| Reporter | Booking-team |
| Blocked by | GW-118 |
| Related | BOOK-412, ADR-0008 |
| Files | `kestrel-web/src/api/types.ts`, `kestrel-web/src/api/wire.ts`, `kestrel-web/src/api/mappers.ts` |

## Description

The web `Shipment` type mirrors the gateway `ShipmentOut` and has no ETA confidence. Once
GW-118 ships we need:

- `ShipmentWire` gets `eta_confidence?: number | null` (snake_case on the wire).
- `Shipment` gets `etaConfidence: number | null` (camelCase in app code).
- The mapper converts between them.
- ShipmentDetail and ShipmentList show a badge: high at or above 0.8, medium 0.5 to 0.79,
  low below 0.5. Copy says "confidence", never "probability" (ADR-0008).

## Acceptance criteria

1. Types and mapper updated; an absent field maps to `null`.
2. Badge renders only when `etaConfidence` is not null.
3. vitest cases for the three bands and the null case.
4. `npm test` is green.
5. No change in behaviour when the gateway does not send the field.

## Comments

**2026-09-19, booking-team:** Raised alongside GW-118.

**2026-09-30, web-team:** Design for the badge approved. Can start once GW-118 is in
staging; mapping and tests can be prepared earlier.

**2026-10-20, web-team:** Still blocked. We will not turn the flag on until all three
tickets (BOOK-412, GW-118, WEB-77) are shipped, per the rollout order.
