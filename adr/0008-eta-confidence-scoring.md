# ADR-0008: ETA confidence scoring

- Status: Accepted
- Date: 2026-09-04
- Deciders: @kestrel/booking-team, @kestrel/web-team, @kestrel/platform-team, @kestrel/architecture-guild

## Context

Shipment `eta` is a single timestamp, but customers treat it as a promise. Support data
for Q2 2026 shows 31% of "where is my shipment" contacts came from ETAs that moved more
than 12 hours. Carriers differ widely in reliability, and ETAs for long multi-leg lanes
are less certain than short ones. We want to show customers how much to trust an ETA
without exposing internal model details.

## Decision

Add a numeric **`eta_confidence`** to the shipment, a double in the range 0..1 where 1 is
"carrier-confirmed and on schedule".

- **Where it is computed:** in booking (`EtaConfidenceScorer`) when building
  `ShipmentResponse`. It starts from the carrier's historical reliability and adjusts for
  lane (domestic bonus, cross-border penalty), time horizon (longer transits score lower),
  load weight (heavy loads score lower) and lifecycle stage (reserved and in-transit
  shipments score higher; delivered is 1.0). The result is clamped to a configured floor and
  ceiling (0.05 and 0.99 by default) and rounded to two decimals.
- **Contract:** `eta_confidence` is added to `GET /v2/shipments/{id}`,
  `POST /v2/shipments` and `POST /v2/shipments/{id}/reserve` responses, snake_case on the
  wire. It is always present once the flag is on.
- **Flag:** `kestrel.booking.features.eta-confidence` gates emission. It defaults to `true`
  in `application.yml` for development; production sets
  `KESTREL_BOOKING_FEATURES_ETA_CONFIDENCE=false` until the consumers are ready.
- **Rollout order:** booking first (BOOK-412), then gateway (GW-118: add the field to
  `ShipmentOut`), then web (WEB-77: add it to the `Shipment` type and render a badge:
  high >= 0.8, medium 0.5 to 0.79, low < 0.5). Flag turned on in production only after
  all three have shipped.

## Consequences

- Positive: customers get a simple trust signal; support can explain moved ETAs.
- Negative: the gateway model is explicit (ADR-0004), so until GW-118 lands the field is
  dropped at the gateway even though booking emits it. WEB-77 is blocked on GW-118 for the
  same reason. As of 2026-10-30 BOOK-412 is done while GW-118 and WEB-77 are open, so the
  production flag must stay off.
- Negative: the score is a heuristic, not a calibrated probability. UI copy must say
  "confidence", never "probability".
- Follow-up: calibrate against actual arrival data after one full quarter of data.
