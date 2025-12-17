# ADR-0003: .NET 8 for the pricing service

- Status: Accepted
- Date: 2025-10-06
- Last amended: 2026-10-06 (PRC-240 reference added)
- Deciders: @kestrel/pricing-team, @kestrel/architecture-guild

## Context

Pricing is a calculation-heavy, read-mostly service. It loads carrier tariffs (some with
hundreds of thousands of rows), applies surcharges and returns a quote with an itemised
breakdown. The team that will own it came from a rating-engine background and works in C#.
Requirements: first-class `decimal` arithmetic (money correctness is the product), low
allocation cost on hot paths, and a simple deploy story.

## Decision

Build pricing in **C# on .NET 8** as a minimal API, namespace `Kestrel.Pricing`, tested with
xunit (`dotnet test`). Contracts:

- `POST /v1/quote` returning `QuoteResponse { quote_id, amount, currency, breakdown[] }`
- `GET /v1/carriers/{code}/surcharges`

Configuration uses the standard `appsettings.json` hierarchy with environment overrides
(`Pricing__FuelSurchargePct` for `Pricing:FuelSurchargePct`). Tariff sources are pluggable
behind `ITariffLoader`; the implementation is chosen by name from the top-level
`"TariffLoader"` configuration key and resolved reflectively by `TariffLoaderFactory`
(`Type.GetType`), so operations can switch sources without a rebuild. Implementations:
`LegacyTariffLoader` (the pipe-delimited export from the old carrier-contract system;
minor-unit amounts; the production setting) and `CsvTariffLoader` (CSV with major-unit
decimals; the factory default, used for carrier onboarding and local development).
Tariff data is embedded in the pricing build, so new tariffs ship with a deploy.

## Consequences

- Positive: `decimal` is a native, 28-digit type; combined with ADR-0005 this removes the
  floating-point class of pricing bugs.
- Negative: loader selection by configuration string means a class can look unreferenced
  to static analysis and to humans. Tooling that deletes "unused" classes will hit
  `LegacyTariffLoader`; see PRC-240 for the time this nearly happened.
- Negative: a third runtime for the platform team to support in on-call.
