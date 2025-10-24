# kestrel-ops

Operational documentation for Kestrel Freight: decisions, incidents, procedures and
policies. There is no code here, apart from one script that renders PDFs.

Kestrel is a freight-booking platform made of four repositories:

| Repository | What it is | Owner |
|---|---|---|
| `kestrel-services/booking` | Java 21 / Spring Boot shipment and reservation service | `@kestrel/booking-team` |
| `kestrel-services/pricing` | .NET 8 quote and tariff service | `@kestrel/pricing-team` |
| `kestrel-services/gateway` | Python / FastAPI public API gateway | `@kestrel/platform-team` |
| `kestrel-web` | TypeScript / React customer UI | `@kestrel/web-team` |
| `kestrel-ops` (this repo) | Documentation | `@kestrel/platform-team`, ADRs: `@kestrel/architecture-guild` |

## Layout

| Path | Contents |
|---|---|
| `adr/` | Nine architecture decision records (0001 to 0009), index in `adr/README.md` |
| `postmortems/` | `2026-03-02-pricing-timeout`, `2026-06-14-double-booking`, `2026-08-21-gateway-429-storm` |
| `runbooks/` | booking-restart, pricing-tariff-reload, gateway-429-storm, rotate-carrier-credentials, db-failover, on-call-handover, deploy-rollback, carrier-onboarding |
| `policies/` | `on-call-policy` (markdown and PDF), `change-management` |
| `sla/` | Carrier SLA summary (markdown and PDF) |
| `tickets/` | `export.csv` of tracked tickets, plus one markdown file per key ticket |
| `scripts/build_pdfs.py` | Renders the two PDFs from their markdown source |
| `glossary.md` | Domain and technical vocabulary |
| `CODEOWNERS` | Review ownership for this repository |

## Where to look first

- "Why does the code do this?" Search `adr/` and `postmortems/`; code `WHY:` comments cite
  ADR numbers (for example ADR-0007 for the carrier rate limiter).
- "Something is on fire." `policies/on-call-policy.md`, then the matching runbook.
- "Can I delete this?" Check the ticket export first. `LegacyTariffLoader` looks unused but
  is loaded by name (PRC-240); `gateway/legacy/pricing_v1.py` really is dead (GW-102).
- "What will my change affect?" ADR-0009 lists owners and how contract changes propagate.

## Rebuilding the PDFs

The PDFs are generated from the markdown; edit the markdown, never the PDF.

```bash
uv run --with reportlab python scripts/build_pdfs.py
```

## Conventions

- Dates are ISO 8601 and times are UTC.
- Ticket ids are cited verbatim (`BOOK-398`, `GW-118`, ...) in code, commits and docs.
- Documents stay under 300 lines; split rather than grow.
- No secrets in this repository. Credentials live in Vault; see
  `runbooks/rotate-carrier-credentials.md`.
- Postmortems are blameless. Accepted ADRs are not rewritten; supersede them.
