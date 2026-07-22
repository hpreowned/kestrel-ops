# Kestrel Carrier SLA Summary

Version 2026.3, effective 2026-09-01. Owner: @kestrel/platform-team. Source of truth for
the commercial terms is each signed carrier agreement; this document summarises the
operational terms engineers need. It is rendered to `carrier-sla.pdf` by
`scripts/build_pdfs.py`.

## 1. Purpose and scope

Kestrel integrates with three carriers: NorthStar Lines (NSL), Baltic Express (BLX) and
Pacific Reach (PCR). This document records the service levels each carrier commits to for
the APIs Kestrel calls (capacity hold, confirmation, cancellation), the rate caps we must
respect, and what Kestrel does in return. Engineers use it to set limits, size timeouts and
decide when a carrier is "degraded" rather than "down".

## 2. Service levels at a glance

| Term | NSL | BLX | PCR |
|---|---|---|---|
| Monthly API availability | 99.5% | 99.9% | 99.0% |
| Capacity-hold p95 latency | 800 ms | 400 ms | 1200 ms |
| Capacity-hold p99 latency | 2000 ms | 900 ms | 3000 ms |
| Contractual request cap | 40 rps | 25 rps | 15 rps |
| Burst allowance | 60 rps for 10 s | 35 rps for 5 s | none |
| Support hours | 24x7 | 07:00 to 19:00 UTC | 06:00 to 18:00 UTC |
| Planned maintenance | Sunday 01:00 to 03:00 UTC | Wednesday 22:00 to 23:00 UTC | first Saturday 00:00 to 04:00 UTC |

The Kestrel booking service applies one limiter bucket per carrier (ADR-0007). The default
rate, `kestrel.booking.ratelimit.per-carrier-rps` = 20, is below the NSL and BLX caps but
above PCR's 15 rps, so PCR carries an override of 8 rps
(`kestrel.booking.ratelimit.overrides.PCR`). Reviewing the other overrides is BOOK-418.

## 3. Availability and credits

Availability is measured by the carrier over calendar months using successful responses
(any non-5xx response within the latency p99) divided by total requests, excluding
planned maintenance and rate-limit rejections caused by Kestrel exceeding the cap.

| Monthly availability (NSL) | Service credit |
|---|---|
| 99.0% to below 99.5% | 5% of monthly fees |
| 98.0% to below 99.0% | 10% of monthly fees |
| Below 98.0% | 25% of monthly fees |

BLX credits start below 99.9% (5%), below 99.5% (15%), below 99.0% (30%). PCR credits start
below 99.0% (5%) and below 97.0% (20%). Kestrel must claim credits within 30 days of the
month end; the platform team compiles evidence from booking metrics.

## 4. Rate limits and throttling

- Carriers return HTTP 429 when we exceed the cap. Sustained breach (more than 2 minutes
  above cap) lets the carrier suspend our credentials for up to 15 minutes.
- Kestrel must never retry a throttled call faster than the `Retry-After` the carrier sends.
- Kestrel's own limiter rejects early with `"carrier capacity exhausted"`; the gateway
  presents this to customers as `"booking temporarily unavailable"`.
- A new carrier's cap must be recorded here before go-live (see
  `runbooks/carrier-onboarding.md`).

## 5. Incident and support response

| Carrier severity | Carrier acknowledges | Carrier target resolution |
|---|---|---|
| Critical (API down) | 15 minutes (NSL), 30 minutes (BLX), 60 minutes (PCR) | 4 hours |
| Major (degraded) | 1 hour | 8 hours |
| Minor | next business day | 5 business days |

Kestrel contact path: platform-team on-call opens the carrier incident through the
carrier's operations portal, then emails the integration contact. Contact addresses are
held in the shared password manager vault "Carrier contacts" (not in this repository).
Integration contacts: NSL carrier-ops team, BLX integration desk, PCR partner support.

## 6. Security and credentials

- API credentials are issued per environment and rotated every 90 days with 24 hours of
  overlap (`runbooks/rotate-carrier-credentials.md`).
- Credentials are stored only in Vault under `secret/kestrel/carriers/<CODE>`.
- Carriers notify Kestrel within 72 hours of any security incident affecting our data.
- Kestrel notifies carriers within 24 hours of suspected credential exposure.

## 7. Data and booking semantics

- A capacity hold is valid for 30 minutes (NSL, BLX) or 20 minutes (PCR) unless confirmed.
- Duplicate holds for one shipment reference are billable as no-shows after the hold
  window: EUR 205 per hold for NSL and BLX, EUR 150 for PCR. Kestrel prevents these with
  the advisory lock in `BookingService.reserve()` (postmortem 2026-06-14).
- Cancellations within 2 hours of confirmation are free; later cancellations follow the
  carrier tariff.
- Amounts in statements are rounded half away from zero to the currency minor unit; this is
  the same rule as ADR-0005.

## 8. Maintenance and change notification

Carriers give at least 7 days' notice of planned maintenance and 30 days for API changes.
Kestrel shifts traffic expectations accordingly: during NSL's Sunday window, booking
errors for NSL are not a Kestrel incident unless they exceed the announced window.

## 9. Kestrel obligations

- Stay under the contractual request cap at all times.
- Pay invoices within 30 days; disputes raised within 45 days of the statement.
- Provide 60 days' notice of forecast volume increases above 25%.
- Keep integration contacts current in the vault.

## 10. Review

Reviewed each quarter by the platform-team with the booking-team. The next review is due
2026-12-01. History:

| Version | Date | Change |
|---|---|---|
| 2026.3 | 2026-09-01 | Added limiter reference after ADR-0007 |
| 2026.2 | 2026-04-15 | Updated PCR availability and credit terms |
| 2026.1 | 2026-01-10 | First consolidated summary |
