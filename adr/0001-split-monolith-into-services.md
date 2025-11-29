# ADR-0001: Split the booking monolith into services

- Status: Accepted
- Date: 2025-09-15
- Last amended: 2026-10-06 (cross-references to later ADRs and incidents added)
- Deciders: @kestrel/architecture-guild, @kestrel/booking-team, @kestrel/pricing-team, @kestrel/platform-team

## Context

Until September 2025 Kestrel ran one deployable, "kestrel-core", a Java application
containing quoting, booking, carrier integration and the customer-facing API. Three
problems pushed us to change that:

- **Release coupling.** A tariff change (pricing) could not ship without a full booking
  regression run. Median lead time for a fuel-surcharge change was 9 days.
- **Scaling shape.** Quote traffic is roughly 14x booking traffic and is CPU-bound, while
  booking is IO-bound on carrier calls and database locks. One deployable meant scaling
  for the worst of both.
- **Ownership blur.** Four teams committed to the same module tree. CODEOWNERS had
  grown to a single `*` line.

We also expect to onboard more carriers in 2026 (see `runbooks/carrier-onboarding.md`),
which multiplies the number of integration points that change independently.

## Decision

Split kestrel-core into three backend services and one frontend, fronted by an API gateway:

| Service | Responsibility | Repo path |
|---|---|---|
| booking | shipments, reservations, carrier capacity holds | `kestrel-services/booking` |
| pricing | quotes, tariffs, surcharges | `kestrel-services/pricing` |
| gateway | public `/api/*` surface, auth, translation of upstream errors | `kestrel-services/gateway` |
| web | customer UI | `kestrel-web` |

Services communicate over HTTP with snake_case JSON. There is no shared database and no
shared library; each service owns its own types. Browsers talk only to the gateway.

Language choices are recorded separately: ADR-0002 (booking), ADR-0003 (pricing),
ADR-0004 (gateway). Ownership is recorded in ADR-0009.

## Consequences

- Positive: independent deploys; pricing ships tariff changes without touching booking.
- Positive: each service scales on its own signal.
- Negative: contract drift becomes possible. A field added in booking is invisible to
  the gateway and web until they are updated (this later happened with `eta_confidence`,
  see ADR-0008, GW-118 and WEB-77).
- Negative: distributed failure modes (timeouts, retry amplification) that did not exist
  in-process. See postmortems 2026-03-02 and 2026-08-21.
- Negative: we operate three runtimes. Mitigated by common runbooks and the change
  management policy (`policies/change-management.md`).
