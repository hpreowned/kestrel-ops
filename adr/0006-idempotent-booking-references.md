# ADR-0006: Idempotent booking references

- Status: Accepted
- Date: 2025-11-10
- Last amended: 2026-06-26 (reference used as lock key, see postmortem)
- Deciders: @kestrel/booking-team, @kestrel/platform-team

## Context

Mobile networks and browser retries mean the same "book this shipment" intent reaches
booking more than once. In kestrel-core each retry created a new shipment, and support
spent roughly two hours a week voiding duplicates. We need retries to be safe at every
hop: web to gateway, gateway to booking, booking to carrier.

## Decision

Every shipment has a public **`reference`** that is derived deterministically from a
caller-supplied **client reference**, so a retry of the same intent maps onto the same
shipment.

- The caller (the web booking form generates one when the form is opened, so a double
  click, refresh or retry reuses it) sends `client_reference` (up to 64 characters) on
  `POST /v2/shipments`.
- Booking derives the public reference as `KB-` plus 12 characters taken from a SHA-256
  of the client reference, for example `KB-7QF2M4X9TB3R`. No client reference means a random
  reference is issued and no idempotency applies.
- `POST /v2/shipments` is idempotent on that reference: a repeat call returns the original
  shipment with `201` and the response header `Idempotent-Replay: true`.
  `shipments.reference` has a unique index.
- `POST /v2/shipments/{id}/reserve` moves a shipment from `CREATED` to `RESERVED`. It is
  **not** idempotent: reserving a shipment that is already `RESERVED`, or in a terminal
  state such as `CANCELLED`, returns 409. After a 409 a caller should `GET` the shipment to
  see its current status.
- The gateway never retries `reserve` automatically (GW-96).

## Consequences

- Positive: retries of creation at any layer are safe, and support can look up by reference.
- Positive: the reference is short and readable on carrier paperwork.
- Negative: the unique index only protects *creation*. It does not serialise concurrent
  `reserve` calls for the same shipment, because reserve is a read-check-write sequence.
  That gap produced the double booking on 2026-06-14 (BOOK-398). The reference is therefore
  also the key of the advisory lock taken inside `BookingService.reserve()`; the reasoning
  is in `postmortems/2026-06-14-double-booking.md`.
- Negative: the losing caller of a concurrent reserve sees 409 even though the shipment
  *is* reserved. UI copy and support scripts must treat that case carefully.
- Negative: callers that reuse a client reference by mistake get surprising "replay"
  behaviour. API docs state that a client reference is single-use per intended shipment.
