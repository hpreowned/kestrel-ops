# Postmortem: Quote timeouts after tariff refresh (2026-03-02)

- Severity: SEV2
- Date of incident: 2026-03-02 (Monday), 08:00 to 09:37 UTC
- Postmortem author: platform-team on-call
- Owner of the fix: @kestrel/pricing-team
- Status: Final

## Summary

At 08:00 UTC the daily tariff roll-out restarted all pricing pods at once. Each pod had to
parse a much larger Baltic Express (`BLX`) tariff file before it could serve, and the
reload blocked request handling. Quote requests took 20 to 40 seconds. The gateway timed
out at 5 seconds and returned 504 to the web app, so customers could not get quotes for
97 minutes.

## Impact

- `POST /api/quote` error rate 71% at peak (08:12), 38% averaged over the incident.
- Roughly 4,900 failed quote requests; an estimated 310 lost bookings.
- Booking itself was healthy; existing shipments were unaffected.

## Timeline (UTC)

| Time | Event |
|---|---|
| 02-27 | BLX publishes tariff v2026-03 with per-postcode zones: 12,000 rows becomes 190,000. |
| 03-02 08:00 | Daily tariff roll-out restarts all 6 pricing pods simultaneously (`maxUnavailable` 100%). |
| 08:04 | Pods saturated parsing the new file; p99 for `/v1/quote` above 30 s. |
| 08:09 | Gateway 504s start; web shows generic error. Support reports. |
| 08:15 | Platform on-call paged by synthetic check; opens incident. |
| 08:31 | Pricing-team engineer identifies refresh storm from logs ("tariff reload started" x6 within one second). |
| 08:52 | Mitigation 1: scale pricing from 6 to 12 pods. Partial relief. |
| 09:20 | Mitigation 2: rolling restart one pod at a time to stagger loads; see `runbooks/pricing-tariff-reload.md`. |
| 09:37 | Error rate under 1%. Incident closed. |

## Root cause

Three causes combined:

1. **Synchronous reload.** The reload parsed and indexed the whole tariff while holding a
   lock; requests queued behind it. There was no previous snapshot to fall back on.
2. **Thundering herd.** The roll-out restarted every pod together, so none could serve
   while the others were loading.
3. **Unreviewed input growth.** BLX's new file was 16x larger and nobody checked load time
   before accepting it. Memory per pod rose from 310 MB to 1.4 GB, causing GC pauses.

The production tariff source is `LegacyTariffLoader`, selected by name in `appsettings.json`
under `"TariffLoader"` (see ADR-0003); the same weakness existed in `CsvTariffLoader`.

## Contributing factors

- Gateway returned a bare 504 without a body, so the web app could not show anything useful.
- No alert on reload duration.
- The gateway timeout (5 s) was shorter than the worst-case reload, so every request on a
  loading pod failed rather than waiting.

## Action items

| Item | Ticket | Owner | Status |
|---|---|---|---|
| `TariffStore.Reload()` builds a complete new index and swaps it in atomically (lock-free reads); roll-outs restart one pod at a time | PRC-211 | @kestrel/pricing-team | Done 2026-03-20 |
| Alert when tariff reload exceeds 5 s; log reload duration | PRC-214 | @kestrel/pricing-team | Done 2026-03-12 |
| Gateway returns a structured 504 body for pricing timeouts | GW-84 | @kestrel/platform-team | Done 2026-03-10 |
| Add a tariff size and load-time check to `runbooks/carrier-onboarding.md` | OPS-38 | @kestrel/platform-team | Done 2026-03-27 |

## Lessons

- Build the new snapshot beside the old one and swap; it is cheaper than any amount of scaling.
- Never restart or reload every instance at once; stagger and jitter.
- Treat partner-supplied files as untrusted input with a size budget.
