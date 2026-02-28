# Postmortem: Double booking on shipment reserve (2026-06-14)

- Severity: SEV2
- Date of incident: 2026-06-14 (Sunday), 13:41 to 16:20 UTC
- Postmortem author: platform-team on-call (primary on the day), reviewed 2026-06-18
- Decision owner for the fix: @kestrel/booking-team
- Status: Final. Action items complete except where noted.
- Follow-up ticket: BOOK-398

This review is blameless. It explains, in one place, **why `BookingService.reserve()` takes
a PostgreSQL advisory lock keyed by the shipment reference**. The code deliberately carries
no comment about it; this document is the reference.

## Summary

Two concurrent `reserve` calls for the same shipment reference both succeeded. Each placed
its own capacity hold with the carrier and each wrote a `RESERVED` event row to `shipment_events`. Over about 2h40m,
23 shipments were reserved twice. Duplicate holds were released manually with the carriers;
two chargeable no-show fees (EUR 410 in total) were incurred. No customer was invoiced twice.

## Impact

- 23 shipments with duplicate carrier capacity holds (NSL 14, BLX 6, PCR 3).
- 2 chargeable hold fees, EUR 410. Remaining holds released without charge.
- 9 customers received two "reservation confirmed" emails.
- Support: 31 tickets. No data loss.

## Timeline (UTC)

| Time | Event |
|---|---|
| 06-09 | booking 1.14.0 deployed. Carrier hold timeout raised from 5 s to 12 s for NSL. |
| 06-14 13:41 | NSL p95 hold latency climbs past 8 s (their weekend maintenance). |
| 13:44 | Gateway `GATEWAY_TIMEOUT_SECONDS` (5 s) expires on slow reserves and the gateway retries the call. The web "Reserve" button is also double-clicked by users waiting for a response. |
| 14:05 | First finance alert: carrier reported a duplicate hold on `KB-3K9T6XQ2M7AD`. |
| 14:20 | Platform on-call paged by support; confirms two reservation rows for one reference. |
| 14:48 | Booking-team engineer joins; reproduces in staging with 2 parallel curl calls. |
| 15:10 | Mitigation: gateway retries disabled with `GATEWAY_RETRY_ATTEMPTS=1`; duplicates drop to near zero. |
| 15:55 | Fix candidate (advisory lock) deployed to staging; 50-way concurrency test clean. |
| 16:20 | Advisory lock released to production as booking 1.14.2. Incident closed. |
| 06-15 to 06-26 | Follow-ups (below). BOOK-398 closed 2026-06-26. |

## Root cause

`reserve()` was a read-check-write sequence:

1. load the shipment, check it can move from `CREATED` to `RESERVED`;
2. call the carrier to place a capacity hold (1 to 12 seconds);
3. set `status = RESERVED` and record a `RESERVED` event row.

Under READ COMMITTED, two calls arriving inside the window of step 2 both saw `CREATED` and
both proceeded. The unique index on `shipments.reference` (ADR-0006) protects creation only;
it does not serialise the state transition. The window was always there but was narrow
when carriers answered in under a second. Longer hold timeouts (1.14.0) plus gateway
retries and user double-clicks made it routine.

## What we tried and rejected

**Optimistic locking (`@Version` on `Shipment`).** Prototyped 2026-06-16. Rejected:

- The conflict is detected at commit, *after* the carrier hold was placed. The losing call
  has therefore already created an external side effect that we would have to compensate by
  cancelling the hold. In staging, 50 concurrent calls produced 11 duplicate holds even
  with correct version checks.
- Compensation is itself a carrier call that can fail or time out, leaving orphan holds.
- The event insert cannot carry a unique constraint: `shipment_events` is an append-only
  history that legitimately holds several rows per shipment.

**Pessimistic row lock (`SELECT ... FOR UPDATE` on the shipment).** Rejected: it blocks
other writers on that row (status updates from the tracking feed, cancellations) for the
full duration of the carrier call, and it does not protect the case where the shipment row
is not yet visible (create immediately followed by reserve under retry).

**Unique constraint on the event or reservation record.** Rejected, see above.

## Decision

Take a **transaction-scoped PostgreSQL advisory lock** keyed by the shipment *reference* at
the start of `BookingService.reserve()`:

- Interface `AdvisoryLock`; production implementation `PostgresAdvisoryLock` executes
  `select pg_advisory_xact_lock(?)` with a 64-bit key (the first 8 bytes of a SHA-256 of a namespaced reference).
- It is transaction scoped, so it is released automatically on commit or rollback. No
  explicit unlock, no leaked locks on pool reuse or crash.
- Keyed by *reference*, not row id, because the reference is the idempotency key every
  layer shares (ADR-0006) and it exists before the row is visible.
- A waiting caller blocks, then re-reads the state: it finds `RESERVED`, is refused with
  409 and does not place a second hold (ADR-0006: reserve is not idempotent).
- The test profile uses `InMemoryAdvisoryLock` (striped `ReentrantLock`s) because H2 has no
  advisory locks.
- Config kill-switch: `kestrel.booking.lock.enabled` (default `true`). Never disable in
  production except as the last step of a documented rollback (`runbooks/deploy-rollback.md`).

Decision owner: `@kestrel/booking-team`, as the owners of `BookingService` (see ADR-0009).
This review was written by platform-team because they were on call.

## Trade-offs accepted

- The lock holds a database connection for the duration of the reserve transaction.
  Mitigated by the per-carrier limiter (ADR-0007), short transactions, and a connection
  pool alarm.
- Callers for the same reference queue instead of failing fast, and the loser gets 409.
  Acceptable: they are retries of the same intent; the UI shows its calm error copy and
  a `GET` shows the true state.

## What went well / badly

- Well: reproduction in staging took under 30 minutes once a booking engineer joined.
- Badly: it took 39 minutes to find the right team; ownership was unclear (led to ADR-0009).
- Badly: no concurrency test existed for `reserve`.

## Action items

| Item | Ticket | Owner | Status |
|---|---|---|---|
| Advisory lock in `BookingService.reserve()` | BOOK-398 | @kestrel/booking-team | Done 2026-06-26 |
| Concurrent reserve test (50 threads, same reference) | BOOK-401 | @kestrel/booking-team | Done 2026-06-30 |
| Alert on advisory lock waits longer than 2 s | BOOK-405 | @kestrel/booking-team | Done 2026-07-08 |
| Gateway must not retry `reserve` on timeout | GW-96 | @kestrel/platform-team | Done 2026-06-22 |
| Disable web Reserve button while a request is in flight | WEB-62 | @kestrel/web-team | Done 2026-06-20 |
| Postmortem template and blameless review process | OPS-44 | @kestrel/platform-team | Done 2026-06-30 |
