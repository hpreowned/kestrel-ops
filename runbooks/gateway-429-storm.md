# Runbook: Gateway 429 / "booking temporarily unavailable"

- Owner: @kestrel/platform-team (gateway), @kestrel/booking-team (limiter)
- Last reviewed: 2026-10-12
- Related: ADR-0007, `postmortems/2026-08-21-gateway-429-storm.md`

## Symptom

- Gateway returns 503 `"booking temporarily unavailable"` with a `Retry-After` header.
  This is the gateway translating booking's `429 "carrier capacity exhausted"` (GW-110).
- Alert "booking 429 rate > 5% for 3 min" fired (OPS-49).
- Customers see `"We couldn't reserve that shipment"` in the web app.

## 1. Find out which carrier

Limiting is per carrier (`CarrierRateLimiter`), so rejections point at one carrier. Booking
counts them in the metric `booking.ratelimit.rejected` with a `carrier` tag:

```bash
for c in NSL BLX PCR; do
  echo -n "$c: "
  kubectl -n kestrel exec deploy/gateway -- \
    curl -fsS "$BOOKING_BASE_URL/actuator/metrics/booking.ratelimit.rejected?tag=carrier:$c" \
    | grep -o '"value":[0-9.]*'
done
```

Or open the dashboard "Booking / Carrier limiter" and look at rejections per carrier.

## 2. Decide

| Observation | Meaning | Action |
|---|---|---|
| Only one carrier rejected, its latency high | Carrier degraded | Step 3, contact the carrier (`sla/carrier-sla.pdf`) |
| All carriers rejected | Bug or config error | Escalate to booking-team immediately |
| Rejections after a config change | Rate set too low | Restore previous value |
| Gateway 503 but booking healthy | Gateway timeout | Check `GATEWAY_TIMEOUT_SECONDS` |

## 3. Reduce pressure (carrier degraded)

Lower, do not raise, the rate for the slow carrier so we stop hammering it. Use the
carrier's override so other carriers keep the default:

```bash
kubectl -n kestrel set env deployment/booking \
  KESTREL_BOOKING_RATELIMIT_OVERRIDES_NSL=5
kubectl -n kestrel rollout status deployment/booking
```

Properties: `kestrel.booking.ratelimit.per-carrier-rps` (default 20, applies to every
carrier) and `kestrel.booking.ratelimit.overrides.<CODE>` (PCR is 8 by default). The
buckets are independent, so other carriers are unaffected. Raising the value above the carrier's
contractual cap risks breaching its SLA terms.

Do **not** disable `kestrel.booking.lock.enabled` to "speed things up". It prevents double
booking (`postmortems/2026-06-14-double-booking.md`).

## 4. Check the gateway

```bash
kubectl -n kestrel get deploy gateway -o jsonpath='{.spec.template.spec.containers[0].env}' \
  | tr ',' '\n' | grep -E "BOOKING_BASE_URL|GATEWAY_TIMEOUT_SECONDS"
```

`GATEWAY_TIMEOUT_SECONDS` defaults to 5. It must exceed booking's normal reserve latency;
raising it only hides trouble. Retries on `reserve` must stay off (GW-96); other idempotent
calls retry up to `GATEWAY_RETRY_ATTEMPTS` (3) times on 502, 503 and 504.

## 5. Communicate

Post status in `#kestrel-incidents` every 15 minutes. If more than 15 minutes, open a
status-page incident. Support template: "Bookings for <carrier> are temporarily limited.
Please try again in a few minutes; your request is not lost."

## Recovery

When carrier latency is back to its SLA p95, remove the override:

```bash
kubectl -n kestrel set env deployment/booking KESTREL_BOOKING_RATELIMIT_OVERRIDES_NSL-
```

## Escalation

`@kestrel/booking-team` for limiter behaviour; `@kestrel/platform-team` for gateway.
SEV1 if all carriers are affected for more than 10 minutes.
