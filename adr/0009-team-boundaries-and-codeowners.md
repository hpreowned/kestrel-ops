# ADR-0009: Team boundaries and CODEOWNERS

- Status: Accepted
- Date: 2026-10-05
- Deciders: @kestrel/architecture-guild, @kestrel/platform-team, @kestrel/booking-team, @kestrel/pricing-team, @kestrel/web-team

## Context

Since the split (ADR-0001) ownership has been informal. It worked while the team was
small, but the 2026-06-14 and 2026-08-21 incidents both lost time to "who decides?":
during the double-booking incident the on-call engineer from platform-team could find
the fix but not who owned the booking locking behaviour; during the 429 storm it took 18
minutes to page the right team. OPS-51 (on-call policy rewrite) needs a definitive map.

## Decision

Ownership follows directories and is enforced with CODEOWNERS in each repository:

| Team | Owns |
|---|---|
| `@kestrel/booking-team` | `kestrel-services/booking` |
| `@kestrel/pricing-team` | `kestrel-services/pricing` |
| `@kestrel/platform-team` | `kestrel-services/gateway`, `kestrel-ops` (runbooks, postmortems), root files of `kestrel-services` |
| `@kestrel/web-team` | `kestrel-web` |
| `@kestrel/architecture-guild` | `kestrel-ops/adr` |

Rules:

1. An owner approves changes in its path. Cross-team changes need both owners.
2. **Behavioural decisions belong to the service owner**, even when another team writes
   the postmortem. The advisory lock in `BookingService.reserve()` is a booking-team
   decision documented by a platform-team postmortem.
3. ADRs are reviewed by the architecture guild; the guild records but does not override
   service-level decisions inside a single service.
4. A contract change in one service names every consuming team on the ticket. If pricing
   changes `/v1/quote`, the gateway (platform-team) and web (web-team, via `/api/quote`)
   are affected and are added as reviewers.
5. The on-call policy escalates to the owning team of the failing path.

## Consequences

- Positive: faster escalation, fewer unowned decisions.
- Negative: shared contract changes require more reviewers; accepted as cheaper than the
  incidents above.
- The root `CODEOWNERS` of this repository applies the table: `/adr/` to the architecture
  guild, everything else to platform-team.
