# Runbook: Roll back a deploy

- Owner: @kestrel/platform-team
- Last reviewed: 2026-10-12
- Related: `policies/change-management.md`

## Decision rule

Roll back first, investigate second, if after a deploy any of these holds for 5 minutes:
error rate above 2%, p95 latency above 2x baseline, readiness failing, or a data-affecting
bug is suspected. Rolling forward is allowed only if the fix is already merged and tested.

## Services

| Service | Release | Rollback command |
|---|---|---|
| booking | `booking` | `helm -n kestrel rollback booking` |
| pricing | `pricing` | `helm -n kestrel rollback pricing` |
| gateway | `gateway` | `helm -n kestrel rollback gateway` |
| web | static assets on CDN | re-point `current` to previous build (below) |

## Steps (backend)

1. Find the previous good revision:
   ```bash
   helm -n kestrel history booking --max 5
   ```
2. Roll back:
   ```bash
   helm -n kestrel rollback booking <REVISION> --wait --timeout 5m
   kubectl -n kestrel rollout status deployment/booking
   ```
3. Verify with the same checks as `booking-restart.md`.
4. Announce in `#kestrel-incidents` and reopen the change ticket.

## Database migrations

Schema changes are forward-only and backward compatible for one release (expand, then
contract). Rolling back the application never rolls back the schema. If a migration is the
cause, escalate to the owning team and do not run manual `drop` statements.

## Config-only rollbacks

For flags, prefer flipping the flag over rolling back the deployment:

- Booking: `KESTREL_BOOKING_FEATURES_ETA_CONFIDENCE=false`
- Gateway: `KESTREL_FEATURE_MULTI_CARRIER_QUOTES=false`
- Pricing: `Pricing__Features__MultiCarrierQuotes=false`
- Web: `VITE_FEATURE_MULTI_CARRIER_QUOTES` is a build-time flag; needs a web rollback.

**Never** set `KESTREL_BOOKING_LOCK_ENABLED=false` as part of a rollback unless the
booking-team lead has approved it in writing; doing so reintroduces the 2026-06-14
double-booking risk. If you must, pause reserve traffic first and record a follow-up.

## Web rollback

```bash
aws s3 cp s3://kestrel-web-releases/previous.txt - | \
  xargs -I{} aws s3 sync s3://kestrel-web-releases/{} s3://kestrel-web-prod/ --delete
```

Then invalidate the CDN cache: `aws cloudfront create-invalidation --distribution-id
"$KESTREL_WEB_DISTRIBUTION" --paths '/*'`.

## After a rollback

Create a ticket for the root cause, link it to the change, and write a postmortem if the
impact was SEV2 or higher.
