# ADR-0007: Rate limit carrier calls per carrier, not globally

- Status: Accepted
- Date: 2026-08-28
- Deciders: @kestrel/booking-team, @kestrel/platform-team, @kestrel/architecture-guild

## Context

Booking calls external carrier APIs (capacity holds, confirmations). Carriers enforce their
own rate limits, and we protect both them and ourselves with a client-side limiter.

Until August 2026 that limiter was a **single global token bucket** (60 requests per second
across all carriers). On 2026-08-21 NorthStar Lines (`NSL`) became slow, with capacity-hold
calls taking 6 to 12 seconds instead of under 1 second. Retries from the gateway and the
web client piled up behind NSL, drained the shared bucket, and booking began answering
`429 "carrier capacity exhausted"` for **every** carrier, including Baltic Express (`BLX`)
and Pacific Reach (`PCR`), whose APIs were healthy. About 55% of booking attempts were
rejected for 47 minutes, and more than 40% of those rejections hit carriers that had no problem at all. The
full account is in `postmortems/2026-08-21-gateway-429-storm.md`.

The incident exposed two properties of a global limiter:

- **Noisy neighbour.** One degraded or chatty carrier consumes the shared budget and starves
  the others. Failure of NSL should degrade NSL bookings, not the whole product.
- **No fit to carrier contracts.** Carrier SLAs differ materially (see `sla/carrier-sla.pdf`):
  contractual request caps are about 40 rps for NSL, 25 for BLX and 15 for PCR, and p95
  response times range from 400 ms to 1200 ms. A single number is either too tight for
  the fast carriers or too loose for the slowest.

Alternatives considered: (a) keep global and raise the limit, which leaves the
noisy-neighbour problem and risks breaching the smallest carrier cap; (b) concurrency
limit (bulkhead) only, which protects threads but does not stop us exceeding a carrier's
rate cap; (c) per-carrier limit combined with the existing bulkhead.

## Decision

Replace the global limiter with **`CarrierRateLimiter`**, which keeps one independent token
bucket per carrier code (`NSL`, `BLX`, `PCR`, and any carrier onboarded later). A call for
carrier X draws only from X's bucket. The refill rate is configured with
`kestrel.booking.ratelimit.per-carrier-rps` (default 20) with optional per-carrier
overrides under `kestrel.booking.ratelimit.overrides.<CODE>`. Bucket capacity is
`burst-seconds` (default 2) times the rate. The default of 20 is below the NSL cap (40)
and BLX cap (25) but above PCR's cap (15), so PCR is overridden to 8, which also respects
its slow p95. When a bucket is empty the request is rejected immediately with
HTTP 429 with a `Retry-After` header and the error string `"carrier capacity exhausted"`;
the string is unchanged so existing alerts and the gateway mapping keep working.
Rejections are counted per carrier in the metric `booking.ratelimit.rejected`
(tag `carrier`).

The gateway translates this 429 into 503 `"booking temporarily unavailable"` (GW-110) and
the web UI shows `"We couldn't reserve that shipment"` without automatic retry (WEB-71),
so a limiter rejection no longer amplifies load.

## Consequences

- Positive: a failing carrier is isolated. With NSL saturated, BLX and PCR bookings
  continue at full rate. This is the headline reason for the change.
- Positive: per-carrier metrics make it obvious which carrier is the problem.
- Negative: total outbound capacity is no longer capped globally. Aggregate load is
  bounded by number of carriers times the rate, so adding carriers raises the ceiling;
  carrier onboarding must review it (`runbooks/carrier-onboarding.md`).
- Negative: the default still ignores SLA differences, so each carrier whose cap or
  latency differs needs an explicit override (today only PCR). Reviewing NSL and BLX
  overrides against their SLAs is tracked in BOOK-418.
- Operational: to ease pressure on a single carrier, lower
  `kestrel.booking.ratelimit.per-carrier-rps` or that carrier's override, see
  `runbooks/gateway-429-storm.md`.
- Implementation tracked as BOOK-409. The class carries a `// WHY:` comment pointing here.
