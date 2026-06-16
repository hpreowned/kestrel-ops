# Runbook: Reload pricing tariffs and change surcharges

- Owner: @kestrel/pricing-team (procedure maintained by @kestrel/platform-team)
- Last reviewed: 2026-10-12
- Related: `postmortems/2026-03-02-pricing-timeout.md`, ADR-0003, PRC-240

## When to use

- A carrier published a new tariff file and it must go live outside the normal deploy.
- The fuel surcharge changes (`Pricing:FuelSurchargePct`).
- Quotes are stale or wrong for one carrier after a tariff update.

## Facts to know first

- Tariffs are loaded by an `ITariffLoader` chosen **by name** from configuration:
  `"TariffLoader": "Kestrel.Pricing.Tariffs.LegacyTariffLoader"` in `appsettings.json`.
  `TariffLoaderFactory` resolves it with `Type.GetType` (and falls back to
  `CsvTariffLoader` when the key is empty). Production uses `LegacyTariffLoader`;
  `CsvTariffLoader` is used for onboarding and local work.
- `LegacyTariffLoader` has no static references and looks dead. **It is not dead and must
  not be deleted or renamed** (PRC-240). Changing the configured name in production
  without a deploy of the new loader will make pricing fail on start-up.
- Tariff data is embedded in the pricing build. `TariffStore.Reload()` builds a complete
  new index and swaps it in atomically, so reads are never blocked (PRC-211). There is no
  HTTP reload endpoint: a reload happens when a pod starts. Reload duration is logged and
  alerted at 5 s (PRC-214).

## Steps: new tariff data

1. New tariff data ships with a pricing release (normal change). Confirm the release is
   deployed and the file is within budget (under 60,000 rows per carrier; larger needs
   pricing-team sign-off).
2. To force pods to pick it up, restart them one at a time; **never restart all pods at
   once** (that was the 2026-03-02 incident):
   ```bash
   for p in $(kubectl -n kestrel get pods -l app=pricing -o name); do
     kubectl -n kestrel delete "$p"
     kubectl -n kestrel wait --for=condition=Ready pod -l app=pricing --timeout=180s
     sleep 30   # jitter so pods do not refresh in lock-step
   done
   ```
3. Watch the logged reload duration and the loaded row count:
   ```bash
   kubectl -n kestrel logs -l app=pricing --since=10m | grep "tariff reload"
   kubectl -n kestrel exec deploy/pricing -- curl -fsS localhost:8082/healthz
   ```
   `/healthz` reports the tariff row count, the active loader type and its source.

## Steps: change fuel surcharge

```bash
kubectl -n kestrel set env deployment/pricing Pricing__FuelSurchargePct=7.5
kubectl -n kestrel rollout status deployment/pricing --timeout=300s
```

(`Pricing__FuelSurchargePct` is the environment form of `Pricing:FuelSurchargePct`.)
Change management applies: a surcharge change is a standard change (see
`policies/change-management.md`).

## Verification

```bash
curl -fsS -X POST "$PRICING_BASE_URL/v1/quote" -H 'content-type: application/json' \
  -d '{"origin":"RTM","destination":"GDN","weight_kg":1200,"carrier_code":"BLX"}'
curl -fsS "$PRICING_BASE_URL/v1/carriers/BLX/surcharges"
```

Expect HTTP 200, `currency` equal to `Pricing:DefaultCurrency`, and a fuel line in
`breakdown`. Unknown carrier must return 422 `"unknown carrier code"`.

## Rollback

`helm rollback pricing` to the previous revision (`deploy-rollback.md`), or set the
previous `Pricing__FuelSurchargePct` value and restart.

## Escalation

`@kestrel/pricing-team` for tariff problems; `@kestrel/platform-team` for cluster issues.
