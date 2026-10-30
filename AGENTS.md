# AGENTS.md — kestrel-ops

<!-- Written by the team. Keep it short; agents read this on every task. Do NOT
     duplicate what pom.xml / csproj / pyproject / package.json / CODEOWNERS encode.
     Backticked paths must exist in THIS repo (lint checks). For paths in another repo
     write `repo:path`, e.g. `kestrel-ops:adr/0007-rate-limit-per-carrier.md`. -->

## Build, test, run, lint
- No code. The only build is `scripts/build_pdfs.py` (regenerates the PDFs in `sla/` and
  `policies/` from their markdown sources; run with `uv run --with reportlab`).
- "Tests" here are link and path checks: every path cited in `tickets/export.csv` must
  exist in the sibling repos.

## Conventions
- ADRs use MADR (`adr/NNNN-slug.md`, status + deciders); postmortems are blameless and
  dated `postmortems/YYYY-MM-DD-slug.md`; runbooks are imperative checklists.
- Ticket ids (`BOOK-`, `PRC-`, `GW-`, `WEB-`, `OPS-`) are the join key to code: cite them.

## Do not touch
- Published PDFs (`sla/carrier-sla.pdf`, `policies/on-call-policy.pdf`) — edit the `.md`
  and rebuild.

## Where things are explained
- This repo *is* the explanation layer: `adr/`, `runbooks/`, `postmortems/`, `tickets/`,
  `glossary.md`. Code lives in the kestrel-services and kestrel-web repos.

<!-- adlc:routing:start -->
## Context routing (kit-owned — do not edit; `adlc init` rewrites this section)

Pick the tool by the shape of the question, not by habit:
- **Graph** (`/graphify query|path|explain`, or `adlc query --level project|org` for
  cross-repo questions): structural questions — who calls this, what breaks if this
  changes, path between two things, which subsystem/community owns it, *why* something
  exists (docs and ADRs are nodes too).
- **grep / file read**: literals — an error string, a config key, a feature flag, a
  column name, a log line. The graph will not beat grep here; do not try.
- **Serena (LSP)**: symbol-precise edits and references — rename, replace a symbol body,
  insert after a symbol, find references across files with type awareness.
- Before trusting the graph run `adlc stale`; exit 0 fresh, 1 usable, 2 rebuild first.
  On a feature branch run `adlc baseline --incremental` before structural queries.
- Levels: this repo's graph answers inside-repo questions; `--level project` answers
  "which consumer breaks"; `--level org` answers "which team/project is affected".
<!-- adlc:routing:end -->

```yaml
adlc:
  schema: 1
  context: [graphify]
  artifact: graphify-out/graph.json
  sensitive: []
  freshness: two-tier
  kit: 0.1.0
```
