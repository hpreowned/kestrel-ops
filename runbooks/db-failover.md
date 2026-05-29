# Runbook: Booking database failover

- Owner: @kestrel/platform-team
- Last reviewed: 2026-10-12
- Applies to: PostgreSQL 15 cluster `booking-pg` (Patroni, one primary, one synchronous replica, one async replica)

## Background

Only booking owns a database (ADR-0001). It also stores the advisory locks that guard
`reserve`; these are held in the primary's memory, so after a failover all locks are gone.
That is safe: in-flight reserves fail with a connection error and are retried by the
caller, and the lock is re-taken by the retry (`postmortems/2026-06-14-double-booking.md`).

## Planned switchover (maintenance)

```bash
kubectl -n data exec -it booking-pg-0 -- patronictl -c /etc/patroni/patroni.yml list
kubectl -n data exec -it booking-pg-0 -- patronictl -c /etc/patroni/patroni.yml \
  switchover --candidate booking-pg-1 --scheduled now
```

Pick the synchronous replica as candidate. Do it outside business hours (02:00 to 04:00
UTC) and as a standard change.

## Unplanned failover

Patroni promotes automatically in about 30 seconds. Confirm, do not fight it:

1. Check roles:
   ```bash
   kubectl -n data exec -it booking-pg-0 -- patronictl -c /etc/patroni/patroni.yml list
   ```
   Exactly one `Leader`; `Lag in MB` of replicas should be 0 to a few MB.
2. If no leader after 2 minutes, page `@kestrel/platform-team` secondary and follow the
   vendor procedure `patronictl failover --candidate <sync-replica> --force`.
3. Booking reconnects through the `booking-pg-rw` service; no config change is needed. If
   connections stay broken after 5 minutes, roll booking (`booking-restart.md`).

## Verify

```bash
kubectl -n data exec -it booking-pg-0 -- psql -U postgres -d booking -c \
  "select count(*) from shipments where created_at > now() - interval '15 minutes';"
kubectl -n data exec -it booking-pg-0 -- psql -U postgres -d booking -c \
  "select pg_is_in_recovery();"      -- must be 'f' on the leader
kubectl -n kestrel exec deploy/gateway -- curl -fsS "$BOOKING_BASE_URL/actuator/health"
```

Then create a test shipment on staging-like canary account and reserve it.

## Data integrity checks after an unplanned failover

If the former primary was async-lagging when it failed, a few seconds of writes may be
lost. Look for shipments that exist at the carrier but not in booking:

- Compare the last 30 minutes of `RESERVED` rows in `shipment_events` against the carrier
  confirmation feed.
- Check for double reservations: `select shipment_id, count(*) from shipment_events
  where event_type = 'RESERVED' group by 1 having count(*) > 1;` Any result is a SEV2:
  escalate to `@kestrel/booking-team`.

## Rollback / reintroduce old primary

Never promote the old primary. Reinitialise it as a replica:
`patronictl -c /etc/patroni/patroni.yml reinit booking-pg booking-pg-0`.

## Escalation

`@kestrel/platform-team` primary on-call. Data inconsistency goes to
`@kestrel/booking-team`. Drill schedule: twice a year; last drill 2026-07-09.
