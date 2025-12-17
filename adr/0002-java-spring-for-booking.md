# ADR-0002: Java 21 and Spring Boot for the booking service

- Status: Accepted
- Date: 2025-09-29
- Deciders: @kestrel/booking-team, @kestrel/architecture-guild

## Context

Booking is the transactional heart of Kestrel: it creates shipments, reserves carrier
capacity and records the result. It needs strong transactional guarantees against
PostgreSQL, mature connection pooling, and good libraries for resilience patterns (token
buckets, circuit breakers). Eight of the eleven engineers who will staff the booking team
already know the JVM from kestrel-core, which was Java 17.

Options considered:

1. **Java 21 + Spring Boot 3.3 + Maven** (extend existing skills).
2. **Kotlin + Ktor.** Pleasant, but only one engineer had production experience.
3. **Go.** Fast and small, but the team would have to rebuild transaction and JPA-style
   mapping tooling that Spring gives us for free.

## Decision

Use **Java 21** with **Spring Boot 3.3.x**, built with **Maven**, base package
`com.kestrel.booking`. Persistence is Spring Data JPA over PostgreSQL 15; schema lives in
`src/main/resources/db/schema.sql`. Tests are JUnit 5 with Spring Boot test and H2 in the
test profile; `mvn -q test` must stay green on main.

JSON on the wire is snake_case, configured once through the Jackson naming strategy rather
than annotating each field.

## Consequences

- Positive: virtual threads (Java 21) remove most of the pain of blocking carrier calls.
- Positive: Spring profiles let us swap infrastructure for tests, for example the
  in-memory advisory lock used by the test profile (see postmortem 2026-06-14).
- Negative: H2 does not support every PostgreSQL feature. Anything that depends on
  Postgres-specific behaviour (advisory locks, `SKIP LOCKED`) needs an abstraction with a
  test double, and a Testcontainers check in CI before release.
- Negative: JVM start-up time (about 14 s) affects restart runbooks; see
  `runbooks/booking-restart.md`.
