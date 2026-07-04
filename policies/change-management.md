# Kestrel Change Management Policy

Version 1.5, effective 2026-10-06. Owner: @kestrel/platform-team.

## 1. Scope

All changes to production: application deploys, configuration (environment variables,
feature flags, `appsettings.json`), infrastructure, database schema and credentials.

## 2. Change types

| Type | Definition | Approval | Examples |
|---|---|---|---|
| Standard | Pre-approved, low risk, runbook exists | Peer review in PR | Fuel surcharge update (`Pricing:FuelSurchargePct`), credential rotation |
| Normal | Needs review and a window | Owning team lead + platform-team | Service deploy with schema change, new carrier |
| Emergency | Needed to stop or prevent an incident | IC decision, review within 2 business days | Rollback, rate limit change during an incident |

## 3. Requirements for every change

1. A ticket (prefix by component: BOOK, PRC, GW, WEB, OPS) linked from the PR.
2. Tests green on the main branch: `mvn -q test` (booking), `dotnet test` (pricing),
   `pytest -q` (gateway), `npm test` (web).
3. A rollback plan, normally `runbooks/deploy-rollback.md`.
4. Owner approval according to `CODEOWNERS` (ADR-0009). Cross-service contract changes
   name every consuming team.
5. For schema changes: expand then contract, backward compatible for one release.

## 4. Protected controls

These need approval from the owning team lead, recorded on the ticket:

- Disabling `kestrel.booking.lock.enabled` (see `postmortems/2026-06-14-double-booking.md`).
- Raising `kestrel.booking.ratelimit.per-carrier-rps` above a carrier's contractual cap.
- Changing which tariff loader is configured (`"TariffLoader"`); see PRC-240.
- Removing any class or module that may be loaded by configuration name. "No references"
  is not proof of dead code; search configuration files first.

## 5. Release rules

- No Normal-change deploys on Fridays after 14:00 UTC or before a public holiday.
- Roll out one environment at a time: staging, then production, with a 30-minute soak.
- Flags that depend on multiple services roll out in dependency order. Example: ADR-0008
  requires booking (BOOK-412), then gateway (GW-118), then web (WEB-77), then the flag.
- Deploys are announced in `#kestrel-deploys`.

## 6. Emergency changes

Allowed during an incident at the IC's discretion. Record the change within one hour,
get a retrospective review within two business days, and add a ticket if the change is to
remain in place.

## 7. Records and audit

Change records are the tickets in `tickets/export.csv` (exported monthly) and PR history.
Finance and the carriers may request records for contractual audits.

## 8. Review

This policy is reviewed twice a year. Proposed edits via PR to `kestrel-ops`, approved by
`@kestrel/platform-team`.

## 9. Change history

| Version | Date | Change |
|---|---|---|
| 1.5 | 2026-10-06 | Config-loaded code rule (PRC-240), flag rollout order (ADR-0008) |
| 1.4 | 2026-07-01 | Added protected controls after the double-booking incident |
| 1.3 | 2026-03-20 | Added tariff size check after the pricing timeout |
| 1.0 | 2025-11-03 | Initial version |
