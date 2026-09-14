# BOOK-377: carriers FK missing on JPA entity

| Field | Value |
|---|---|
| Status | open |
| Component | booking |
| Owner team | @kestrel/booking-team |
| Created | 2026-05-19 |
| Closed | |
| Reporter | Booking engineer |
| Related | ADR-0002 |
| Files | `booking/src/main/resources/db/schema.sql`, `booking/src/main/java/com/kestrel/booking/domain/Shipment.java` |

## Description

`db/schema.sql` declares `shipments.carrier_id bigint REFERENCES carriers(id)`, so the
database enforces that every shipment points at a real carrier. The JPA `Shipment` entity
declares only `private Long carrierId;` with no `@ManyToOne` or `@JoinColumn`. As a result:

- Hibernate does not know about the relationship; joins to carriers are hand-written.
- `carrier_code` in `ShipmentResponse` is resolved with an extra lookup per shipment.
- Schema generation or validation in tests (H2) cannot detect a broken relation.

## Acceptance criteria

1. `Shipment` maps the relationship (`@ManyToOne(fetch = LAZY)` with
   `@JoinColumn(name = "carrier_id")`) to a `Carrier` entity.
2. The JSON contract (`carrier_code`, snake_case) is unchanged.
3. No N+1 query when listing shipments (fetch join or batch size verified in a test).
4. Existing `carrierId` usages are migrated or kept as a read-only column mapping.
5. `mvn -q test` is green.

## Comments

**2026-05-19, booking-team:** Found while writing the carrier summary query.

**2026-06-02, booking-team:** Deprioritised behind the Q2 carrier summary release; no customer
impact, only code quality and an extra query.

**2026-09-28, booking-team:** Still wanted. Pairs naturally with per-carrier overrides
(BOOK-418).
