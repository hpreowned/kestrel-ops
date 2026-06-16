# Runbook: Rotate carrier API credentials

- Owner: @kestrel/platform-team
- Last reviewed: 2026-10-12
- Cadence: every 90 days, or immediately on suspected exposure
- Related: OPS-53 (rotation reminders)

## Rules

- Credentials live only in Vault under `secret/kestrel/carriers/<CODE>`, where `<CODE>` is
  `NSL`, `BLX` or `PCR`. They are never committed, pasted into chat, tickets or logs.
- Read new secrets from stdin or a protected file, never from a command-line argument
  (shell history).
- Two people: one rotates, one verifies (four-eyes), per `policies/change-management.md`.

## Steps

1. Raise a standard change with the carrier code and a 30-minute window.
2. Ask the carrier's integration contact (see `sla/carrier-sla.pdf`) to issue a new client
   secret while keeping the old one valid for overlap (all three carriers support 24 h).
3. Store the new secret without exposing it on the command line:
   ```bash
   vault login -method=oidc
   vault kv patch secret/kestrel/carriers/NSL client_secret=-
   # paste the secret, press Ctrl-D
   vault kv metadata get secret/kestrel/carriers/NSL | grep -E "current_version|created_time"
   ```
4. Make booking pick it up. Credentials are read at start-up; roll booking
   (`booking-restart.md`):
   ```bash
   kubectl -n kestrel rollout restart deployment/booking
   kubectl -n kestrel rollout status deployment/booking --timeout=300s
   ```
5. Verify with a real capacity check on staging first, then production:
   ```bash
   kubectl -n kestrel logs -l app=booking --since=5m | grep -E "carrier=NSL.*(auth|401|403)"
   ```
   No output means no authentication failures. Also make one test reservation.
6. After 24 h with no auth errors, ask the carrier to revoke the old secret.
7. Record the new `current_version` in the change ticket (never the value).

## Rollback

Within the overlap window, `vault kv rollback -version=<previous> secret/kestrel/carriers/NSL`
and restart booking.

## If a secret was exposed

Treat as SEV2: rotate immediately without overlap, then follow `policies/on-call-policy.md`
for incident handling and notify the carrier.

## Escalation

`@kestrel/platform-team` on-call; carrier security contacts are in the SLA document.
