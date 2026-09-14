# BOOK-412: Add eta_confidence to the /v2/shipments response

| Field | Value |
|---|---|
| Status | done |
| Component | booking |
| Owner team | @kestrel/booking-team |
| Created | 2026-09-03 |
| Closed | 2026-09-18 |
| Reporter | Product (customer support insights) |
| Related | ADR-0008, GW-118, WEB-77 |
| Files | `booking/src/main/java/com/kestrel/booking/web/dto/ShipmentResponse.java`, `booking/src/main/java/com/kestrel/booking/service/EtaConfidenceScorer.java`, `booking/src/main/resources/application.yml` |

## Description

Customers treat `eta` as a promise, but carriers' reliability varies. Add a numeric
`eta_confidence` (double, 0..1) to every `ShipmentResponse` so clients can show how much to
trust the ETA. Scoring rules are defined in ADR-0008. The field is serialised snake_case
by the existing Jackson naming strategy. Emission is behind the property
`kestrel.booking.features.eta-confidence` (`true` in `application.yml`; production sets it to false until consumers are ready).

Endpoints affected: `POST /v2/shipments`, `GET /v2/shipments/{id}`,
`POST /v2/shipments/{id}/reserve`.

## Acceptance criteria

1. `ShipmentResponse` JSON contains `eta_confidence` as a number between 0 and 1 inclusive
   when the flag is on; the field is absent (or null) when it is off.
2. Score is clamped and rounded to two decimals.
3. `EtaConfidenceScorer` combines carrier reliability, lane, time horizon, weight and
   lifecycle stage, clamped to a floor and ceiling (ADR-0008).
4. Unit tests for the boundaries: floor, ceiling, delivered (1.0), long transit, heavy load.
5. `mvn -q test` is green.
6. Consumers notified: gateway and web tickets raised before merge.

## Comments

**2026-09-04, booking-team:** Implemented behind the flag; no behaviour change when off.

**2026-09-10, platform-team:** Heads-up: the gateway's `ShipmentOut` model is explicit
(ADR-0004), so `eta_confidence` will be dropped there until GW-118 is done. Please keep
the flag off in production until the gateway and web follow.

**2026-09-14, booking-team:** Agreed. Rollout order is booking, gateway, web, then flag.

**2026-09-18, booking-team:** Merged and released in booking 1.17.0. Closing as done.
GW-118 and WEB-77 raised for the consumers.
