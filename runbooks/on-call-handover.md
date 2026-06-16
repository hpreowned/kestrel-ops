# Runbook: On-call handover

- Owner: @kestrel/platform-team
- Last reviewed: 2026-10-12
- Policy: `policies/on-call-policy.md` (rewritten under OPS-51, effective 2026-10-01)

Handover happens every Monday at 10:00 UTC, in a 15-minute call or, if both agree, in
writing in `#kestrel-oncall`. The outgoing primary owns the handover; the incoming primary
confirms receipt.

## Outgoing engineer checklist

1. Open incidents: list each with owner, current state, next action.
2. Silenced or snoozed alerts and when they expire.
3. Changes in flight or scheduled this week (change calendar).
4. Known flaky things: for example "NSL latency spikes Sunday evenings".
5. Any manual mitigation still in place, especially config overrides:
   ```bash
   kubectl -n kestrel get deploy booking pricing gateway -o yaml \
     | grep -E "RATELIMIT|LOCK_ENABLED|FUEL|TIMEOUT" 
   ```
   Every override must have a ticket and an owner. `kestrel.booking.lock.enabled` must be
   `true`.
6. Pending postmortems and action items due this week.

## Incoming engineer checklist

1. Confirm you can be paged: use the paging tool's "test notification" and acknowledge it.
2. Confirm access: `kubectl auth can-i get pods -n kestrel`, Vault login, dashboards.
3. Read the last three entries of `postmortems/` if you have not before.
4. Know who your secondaries are and who owns each service (`CODEOWNERS`, ADR-0009).
5. Post "On-call primary: <name>, secondary: <name>" in `#kestrel-oncall`.

## Template for the written handover

```text
Handover <date> from <outgoing> to <incoming>
Open incidents: ...
Overrides in place: ... (ticket, owner, expiry)
Changes this week: ...
Watch list: ...
Action items due: ...
```

## Swaps and absences

Swaps are agreed in `#kestrel-oncall` and updated in the paging tool before the swap
starts. Nobody is on call without an acknowledged handover.

## Escalation

If the outgoing engineer cannot be reached and incidents are open, the incoming engineer
escalates to the platform-team lead.
