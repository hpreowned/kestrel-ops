# Runbook: Restart the booking service

- Owner: @kestrel/booking-team (procedure maintained by @kestrel/platform-team)
- Last reviewed: 2026-10-12
- Severity it is used for: SEV2 and below; for SEV1 also follow `policies/on-call-policy.md`

## When to use

- Booking readiness is failing or p95 latency has regressed and a restart is the agreed fix.
- A config change that is only read at start-up (rate limit, feature flag, lock toggle).

Do **not** restart booking to "clear" 429s. Those come from the carrier limiter; see
`gateway-429-storm.md`.

## Background

JVM start-up takes about 14 seconds before readiness (booking listens on port 8081). In-flight `reserve` calls hold a
PostgreSQL advisory lock (transaction scoped); if a pod dies the connection drops and
PostgreSQL releases the lock, so a restart cannot leave a stuck lock. Postmortem:
`postmortems/2026-06-14-double-booking.md`.

## Pre-checks

```bash
kubectl config use-context kestrel-prod-eu1
kubectl -n kestrel get deploy booking -o wide
kubectl -n kestrel get pods -l app=booking
# lock must be enabled; if this prints false, stop and escalate to booking-team
kubectl -n kestrel exec deploy/booking -- printenv KESTREL_BOOKING_LOCK_ENABLED
```

## Steps

1. Announce in `#kestrel-incidents`: "restarting booking, rolling, ETA 5 min".
2. Roll one pod at a time (the deployment uses `maxUnavailable: 0`):
   ```bash
   kubectl -n kestrel rollout restart deployment/booking
   kubectl -n kestrel rollout status deployment/booking --timeout=300s
   ```
3. If you changed config first, set it with `kubectl set env` (Spring relaxed binding):
   ```bash
   kubectl -n kestrel set env deployment/booking \
     KESTREL_BOOKING_FEATURES_ETA_CONFIDENCE=false
   ```
   Property names map as `kestrel.booking.ratelimit.per-carrier-rps` to
   `KESTREL_BOOKING_RATELIMIT_PER_CARRIER_RPS`.

## Verification

```bash
kubectl -n kestrel exec deploy/gateway -- \
  curl -fsS "$BOOKING_BASE_URL/actuator/health/readiness"
kubectl -n kestrel exec deploy/gateway -- \
  curl -fsS "$BOOKING_BASE_URL/v2/carriers" | head -c 300
```

- All pods `READY 1/1`, no restarts after the roll.
- Dashboard "Booking / Carrier limiter": rejections per carrier back to ~0.
- No sessions stuck waiting on advisory locks:
  `select count(*) from pg_stat_activity where wait_event = 'advisory';` returns 0.

## Rollback

If new pods fail readiness, `kubectl -n kestrel rollout undo deployment/booking`, then
follow `deploy-rollback.md`.

## Escalation

Page `@kestrel/booking-team` through the paging tool if readiness does not return within 10
minutes or any pod shows `KESTREL_BOOKING_LOCK_ENABLED=false`.
