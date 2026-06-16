# Runbook: Onboard a new carrier

- Owner: @kestrel/platform-team with @kestrel/booking-team and @kestrel/pricing-team
- Last reviewed: 2026-10-12
- Related: ADR-0007, ADR-0003, `sla/carrier-sla.pdf`, OPS-38

Existing carriers: NorthStar Lines (`NSL`), Baltic Express (`BLX`), Pacific Reach (`PCR`).
Allow two weeks end to end. A carrier code is exactly three upper-case letters.

## 1. Commercial and SLA

- Signed agreement and SLA recorded in `sla/carrier-sla.md` (availability, p95 latency, rate
  cap, support hours, maintenance windows).
- Obtain the contractual **request cap** in rps. The limiter must sit below it.

## 2. Credentials

Follow `rotate-carrier-credentials.md` for storage: Vault path
`secret/kestrel/carriers/<CODE>`. Test credentials first, production second.

## 3. Booking changes (booking-team)

- Add the carrier row (`carriers` table) via a migration; record its id.
- Implement the carrier client adapter; contract-test against the carrier sandbox.
- Rate limiting is per carrier (ADR-0007): the new carrier automatically gets its own
  `CarrierRateLimiter` bucket at `kestrel.booking.ratelimit.per-carrier-rps` (default 20).
  If the contractual cap is below that value (as for PCR, cap 15, override 8), add
  `kestrel.booking.ratelimit.overrides.<CODE>`.
- Re-check aggregate outbound load: buckets add up across carriers.

## 4. Pricing changes (pricing-team)

1. Prepare the tariff in the CSV layout `carrier_code,zone,min_kg,max_kg,base_amount,per_kg`
   (zones D, R, I; major-unit decimals). The production `LegacyTariffLoader` reads the
   pipe-delimited form with integer minor units; convert, do not hand-edit.
2. **Size and load budget (OPS-38):** under 60,000 rows and reload under 5 s locally:
   ```bash
   wc -l <CODE>-tariff.csv
   # load it on a staging pod and read the duration from the log
   kubectl -n kestrel-staging logs -l app=pricing --since=5m | grep "tariff reload finished"
   ```
3. Check surcharges: `GET /v1/carriers/<CODE>/surcharges`.
4. Production loader remains `LegacyTariffLoader` (configured by name, see PRC-240); the
   new carrier's rows are added to the embedded export and shipped with a pricing release.

## 5. Gateway and web

- `GET /api/carriers` reflects booking's list; no gateway change needed unless the carrier
  has special fields.
- Web displays carriers from the API. With `Pricing:Features:MultiCarrierQuotes` /
  `KESTREL_FEATURE_MULTI_CARRIER_QUOTES` on, the new carrier appears in comparison quotes.

## 6. Smoke tests (staging, then production)

```bash
curl -fsS "$BOOKING_BASE_URL/v2/carriers" | grep -c "<CODE>"
curl -fsS -X POST "$PRICING_BASE_URL/v1/quote" -H 'content-type: application/json' \
  -d '{"origin":"RTM","destination":"GDN","weight_kg":800,"carrier_code":"<CODE>"}'
```

Then create and reserve one shipment through `/api/shipments` and
`/api/shipments/{id}/reserve`.

## 7. Go live

Change ticket approved, on-call told, first 24 hours monitored on the "Booking / Carrier
limiter" dashboard. Update `glossary.md` and the carrier table in `sla/carrier-sla.md`, then
regenerate the PDF with `uv run --with reportlab python scripts/build_pdfs.py`.
