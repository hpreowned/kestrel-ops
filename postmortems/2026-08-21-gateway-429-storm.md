# Postmortem: Gateway 429 storm (2026-08-21)

- Severity: SEV1
- Date of incident: 2026-08-21 (Friday), 09:14 to 10:01 UTC (47 minutes)
- Postmortem author: platform-team on-call, reviewed 2026-08-26
- Owner of the fix: @kestrel/booking-team (limiter), @kestrel/platform-team (gateway)
- Status: Final. Led to ADR-0007.

## Summary

NorthStar Lines (`NSL`) became slow. Retries piled onto booking's single global rate-limit
bucket, which then rejected requests for **all** carriers with `429 "carrier capacity
exhausted"`. The gateway passed the 429 through; the web app retried automatically three
times with no backoff, which tripled the load and kept the bucket empty.

## Impact

- 5,120 booking and reserve attempts in the window; 2,816 (55%) rejected.
- 1,206 of those rejections (43%) were for BLX and PCR, whose carriers were healthy.
- Estimated 640 abandoned bookings. No data loss, no duplicate bookings (the advisory lock
  from the 2026-06-14 incident held under the load).

## Timeline (UTC)

| Time | Event |
|---|---|
| 09:02 | NSL capacity-hold latency rises from 0.7 s to 6 s. |
| 09:14 | Global limiter (60 rps) empties; first 429s. Alert "booking 429 rate" does not exist yet. |
| 09:19 | Support reports that "all carriers fail". Platform on-call paged. |
| 09:27 | On-call checks gateway; sees 429 passthrough, assumes gateway rate limiting, loses 10 minutes. |
| 09:37 | Booking-team paged (18 minutes after first report; ownership unclear). |
| 09:44 | Booking engineer identifies the global bucket and NSL latency. |
| 09:51 | Mitigation: global bucket raised from 60 to 120 rps by hotfix config and NSL bookings paused; BLX and PCR recover. |
| 10:01 | NSL recovers on its own; incident closed. |
| 08-22 | Tickets opened for the actions below. |

## Root cause

A **single global token bucket** shared by all carriers. One slow carrier raised in-flight
time, retries added load, the bucket drained, and every carrier was rejected. This is the
noisy-neighbour failure ADR-0007 addresses: the limiter is now per carrier
(`CarrierRateLimiter`, key `kestrel.booking.ratelimit.per-carrier-rps`).

Amplifiers:

- The gateway returned the upstream 429 unchanged. The error string `"carrier capacity
  exhausted"` was meaningless to customers. The gateway now translates it into 503
  `"booking temporarily unavailable"` with a `Retry-After` header (GW-110).
- The web client retried 429 and 5xx automatically with no backoff. It now shows
  `"We couldn't reserve that shipment"` and does not retry reserve automatically (WEB-71).
- No alert existed on the 429 rate.
- On-call did not know who owned booking limits (see ADR-0009 and OPS-51).

## What went well

- The advisory lock prevented duplicates under 3x retry load.
- Per-carrier error rates were easy to reconstruct from booking logs.

## Action items

| Item | Ticket | Owner | Status |
|---|---|---|---|
| Replace global limiter with per-carrier `CarrierRateLimiter` | BOOK-409 | @kestrel/booking-team | Done 2026-09-01 |
| Gateway: translate upstream 429 to 503 "booking temporarily unavailable" | GW-110 | @kestrel/platform-team | Done 2026-08-25 |
| Web: no automatic retry on reserve; calm error copy | WEB-71 | @kestrel/web-team | Done 2026-08-30 |
| Alert when booking 429 rate exceeds 5% for 3 minutes | OPS-49 | @kestrel/platform-team | Done 2026-08-27 |
| Rewrite on-call policy with explicit escalation by owning team | OPS-51 | @kestrel/platform-team | Done 2026-10-01 |
| Review NSL and BLX rps overrides against their SLA caps | BOOK-418 | @kestrel/booking-team | Open |

## Lessons

- Isolate failure domains: one carrier's slowness must not consume another's budget.
- Rejecting early is good; rejecting with a message customers act on is better.
- Never auto-retry a non-idempotent action without backoff and a budget.
