# Glossary

Terms used across Kestrel code, tickets and runbooks. Identifiers are written exactly as
they appear in code or configuration.

## Business terms

| Term | Meaning |
|---|---|
| Carrier | A freight company that moves shipments. Kestrel integrates with three: NSL, BLX, PCR. |
| NSL | NorthStar Lines. Largest carrier by volume (about 55% of bookings). Broad network, mid-priced. |
| BLX | Baltic Express. Fast API, highest availability SLA, tightest p95. |
| PCR | Pacific Reach. Lowest contractual request cap (15 rps), slowest API. |
| Shipment | A booking request moving goods from origin to destination via one carrier. Statuses: `CREATED`, `RESERVED`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`. |
| Reference | Public shipment id of the form `KB-` plus 12 characters, derived from the caller's `client_reference` so retries map to one shipment (ADR-0006). |
| Reserve | Place a capacity hold with the carrier and mark the shipment `RESERVED`. |
| Capacity hold | A temporary claim on carrier space; valid 20 to 30 minutes unless confirmed. |
| Quote | A priced offer with an itemised `breakdown`; produced by pricing. |
| Tariff | A carrier's rate table (per kg, per zone). Loaded by an `ITariffLoader`. |
| Fuel surcharge | Percentage added to base freight; config `Pricing:FuelSurchargePct`. |
| Minor unit | Smallest currency unit (cent). Money is stored and compared in minor units (ADR-0005). |

## Technical terms

| Term | Meaning |
|---|---|
| `eta_confidence` | Double 0..1 trust score for a shipment's ETA (ADR-0008, BOOK-412, GW-118, WEB-77). |
| `AdvisoryLock` | Interface in booking used by `BookingService.reserve()`; `PostgresAdvisoryLock` runs `pg_advisory_xact_lock`; `InMemoryAdvisoryLock` is the test profile double. See postmortem 2026-06-14. |
| `kestrel.booking.lock.enabled` | Property that toggles the advisory lock. Keep `true` in production. |
| `CarrierRateLimiter` | Per-carrier token bucket in booking (ADR-0007). |
| `kestrel.booking.ratelimit.per-carrier-rps` | Refill rate of each carrier's bucket; default 20. Per-carrier values go under `kestrel.booking.ratelimit.overrides.<CODE>` (PCR: 8). |
| `kestrel.booking.features.eta-confidence` | Property gating emission of `eta_confidence`. |
| "carrier capacity exhausted" | Booking's 429 error string when a carrier bucket is empty. |
| "booking temporarily unavailable" | Gateway's 503 message translating that 429 (GW-110). |
| `ShipmentOut` | Gateway Pydantic response model for shipments (`gateway/gateway/models.py`). |
| `Money.Round` | Pricing's rounding helper: `MidpointRounding.AwayFromZero`. |
| `LegacyTariffLoader` | Production `ITariffLoader` reading the pipe-delimited legacy export; selected by name in `appsettings.json` and resolved with `Type.GetType`. Not dead code (PRC-240). |
| `CsvTariffLoader` | CSV `ITariffLoader` (major-unit decimals), the factory default; for onboarding and local use. |
| `TariffLoaderFactory` | Resolves the configured loader name to an instance. |
| `BOOKING_BASE_URL` / `PRICING_BASE_URL` | Gateway env vars locating booking and pricing. |
| `GATEWAY_TIMEOUT_SECONDS` | Gateway upstream timeout (default 5). |
| `KESTREL_FEATURE_MULTI_CARRIER_QUOTES` | Gateway flag; pricing equivalent `Pricing:Features:MultiCarrierQuotes`; web `VITE_FEATURE_MULTI_CARRIER_QUOTES`. |

## Process terms

| Term | Meaning |
|---|---|
| ADR | Architecture decision record in `adr/` (MADR format). |
| Postmortem | Blameless incident review in `postmortems/`. |
| Runbook | Step-by-step operational procedure in `runbooks/`. |
| IC | Incident commander; the on-call primary by default. |
| SEV1 to SEV4 | Incident severities defined in `policies/on-call-policy.md`. |
| Standard / Normal / Emergency change | Change types in `policies/change-management.md`. |
| Primary / secondary | On-call roles, both from platform-team. |

## Ticket prefixes

`BOOK` booking, `PRC` pricing, `GW` gateway, `WEB` web, `OPS` operations and policy.
Status values in `tickets/export.csv`: `open`, `done` (delivered work), `closed` (follow-up
or decision closed; includes won't-do such as PRC-240).
