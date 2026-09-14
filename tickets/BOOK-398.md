# BOOK-398: Double booking incident follow-up (advisory lock)

| Field | Value |
|---|---|
| Status | closed |
| Component | booking |
| Owner team | @kestrel/booking-team |
| Created | 2026-06-14 |
| Closed | 2026-06-26 |
| Reporter | Platform on-call |
| Related | postmortems/2026-06-14-double-booking.md, ADR-0006, BOOK-401, BOOK-405, GW-96, WEB-62 |
| Files | `booking/src/main/java/com/kestrel/booking/service/BookingService.java`, `booking/src/main/java/com/kestrel/booking/lock/AdvisoryLock.java`, `booking/src/main/java/com/kestrel/booking/lock/PostgresAdvisoryLock.java`, `booking/src/main/java/com/kestrel/booking/lock/InMemoryAdvisoryLock.java` |

## Description

On 2026-06-14, two concurrent `reserve` calls for the same shipment reference both
succeeded and placed duplicate carrier holds (23 shipments). Prevent concurrent reserves
for the same reference from interleaving.

## Acceptance criteria

1. `BookingService.reserve()` acquires a lock keyed by the shipment reference before the
   status check and holds it until the transaction ends.
2. The lock is an `AdvisoryLock` interface with a `PostgresAdvisoryLock` implementation
   (`select pg_advisory_xact_lock(?)`) and an `InMemoryAdvisoryLock` for the test profile.
3. A property `kestrel.booking.lock.enabled` (default true) toggles it.
4. The second concurrent caller observes `RESERVED` and is refused with 409; it does not
   claim carrier capacity a second time.
5. Concurrency test with 50 threads on one reference (BOOK-401).

## Comments

**2026-06-16, booking-team:** Spike with `@Version` optimistic locking: 11 duplicate holds
in 50 concurrent calls because the conflict surfaces after the carrier hold. Rejected.

**2026-06-19, platform-team:** Agree. Pessimistic `FOR UPDATE` blocks tracking-feed
updates for the whole carrier call; advisory lock avoids that. Details are in the
postmortem.

**2026-06-24, booking-team:** Merged, released as booking 1.14.2 after staging soak.

**2026-06-26, booking-team:** Closing. Follow-ups BOOK-401, BOOK-405 done or scheduled.
Decision owner for the lock is booking-team (ADR-0009).
