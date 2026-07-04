# Kestrel On-Call Policy

Version 3.0, effective 2026-10-01. Owner: @kestrel/platform-team. Replaces version 2.1
(OPS-51, closed 2026-10-01). Reviewed every six months.

## 1. Purpose

This policy defines who is on call for Kestrel production, how incidents are classified,
how quickly we respond, and how we escalate to the team that owns the failing code. It
exists because two incidents in 2026 (double booking on 2026-06-14, gateway 429 storm on
2026-08-21) lost time finding the right people.

## 2. Rotation

- Two roles each week: **primary** and **secondary**, both from `@kestrel/platform-team`.
- Weeks run Monday 10:00 UTC to Monday 10:00 UTC. Handover follows
  `runbooks/on-call-handover.md`.
- Booking, pricing and web each name one **service contact** per week who can be paged
  for questions about their service. Service contacts are not first responders.
- Engineers join the rotation after shadowing two weeks and completing the runbook
  walk-through (db-failover and deploy-rollback drills).
- Maximum of one primary week in four. Nobody is primary two weeks running.

## 3. Severity levels

| Level | Definition | Examples |
|---|---|---|
| SEV1 | Customers cannot book or get quotes at all, or data is being corrupted | All carriers rejected; database down |
| SEV2 | Major degradation for many customers or one carrier fully down | Quote error rate over 20%; duplicate reservations |
| SEV3 | Minor degradation with a workaround | One page slow; delayed notification |
| SEV4 | No customer impact | Alert noise, cosmetic defect |

When unsure, pick the higher severity and downgrade later.

## 4. Response targets

| Level | Acknowledge | First update | Updates | Postmortem |
|---|---|---|---|---|
| SEV1 | 5 minutes | 15 minutes | every 15 minutes | within 5 business days |
| SEV2 | 15 minutes | 30 minutes | every 30 minutes | within 5 business days |
| SEV3 | 4 business hours | next business day | as needed | optional |
| SEV4 | next business day | n/a | n/a | no |

Targets apply 24x7 for SEV1 and SEV2.

## 5. Escalation by owning team

The primary escalates to the team that owns the failing path as defined in `CODEOWNERS`
and ADR-0009. Do not wait to prove the cause before paging.

| Symptom area | Page |
|---|---|
| Reservations, carriers, rate limiter, advisory lock | `@kestrel/booking-team` |
| Quotes, tariffs, surcharges, rounding | `@kestrel/pricing-team` |
| Gateway errors, timeouts, translation | `@kestrel/platform-team` (secondary) |
| UI errors | `@kestrel/web-team` |
| Architecture or cross-service decision | `@kestrel/architecture-guild` (next business day) |

Page the owning team after **10 minutes** without a clear owner-independent fix for SEV1,
and after **20 minutes** for SEV2. The primary stays incident commander until the incident
is handed off explicitly.

## 6. Incident roles

- **Incident commander (IC):** the primary by default. Coordinates, decides, communicates.
- **Operations lead:** hands-on fixer, typically from the owning team.
- **Communications:** posts in `#kestrel-incidents` and the status page; for SEV1 a
  secondary takes this role.

## 7. During an incident

1. Acknowledge the page and open a thread in `#kestrel-incidents` with severity.
2. Stabilise first: mitigate (roll back, flip flag, lower rate) before root-causing.
3. Keep a timeline in UTC in the thread.
4. Any manual override gets a ticket, an owner and an expiry.
5. Never disable safety controls such as `kestrel.booking.lock.enabled` without the
   booking-team lead's written approval.
6. Close with a summary and the customer-facing statement.

## 8. Postmortems

Blameless and written within five business days for SEV1 and SEV2, using the template
from OPS-44. File as `postmortems/YYYY-MM-DD-slug.md`. Every action item has a ticket and
an owner. The owning team of the code decides the remediation; the author may be anyone.

## 9. Load and fairness

- On-call hours outside 08:00 to 20:00 local time earn compensatory time off.
- After a page between 00:00 and 06:00 local time, the engineer starts late the next day.
- If a week has more than 5 out-of-hours pages, platform-team leadership reviews whether
  the alert set needs tuning.

## 10. Contacts

- Paging: the paging tool's `kestrel-primary` and `kestrel-secondary` schedules.
- Chat: `#kestrel-oncall` (coordination), `#kestrel-incidents` (live incidents).
- Carrier escalation contacts: `sla/carrier-sla.pdf`.

## 11. Change history

| Version | Date | Change |
|---|---|---|
| 3.0 | 2026-10-01 | Rewrite: owner-based escalation, explicit timers (OPS-51) |
| 2.1 | 2026-02-12 | Added secondary role |
| 2.0 | 2025-11-03 | Split from kestrel-core on-call after ADR-0001 |
