# Graph Report - kestrel-ops  (2026-10-30)

## Corpus Check
- Corpus is ~15,403 words - fits in a single context window. You may not need a graph.

## Summary
- 150 nodes · 168 edges · 22 communities (11 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- PDF Build Pipeline
- ADLC CI Automation
- API Contract ETA Confidence
- Tariff and Pricing Operations
- Carrier Limits and Money
- On-Call Ownership Escalation
- Booking Service Operations
- ADLC Workflow Triggers
- Idempotent Reservation Safety
- Production Change Controls
- Dependency Update Configuration
- ADR Catalog
- Documentation Governance
- Freight Domain Glossary
- Platform Architecture Overview
- Database Failover Integrity
- Backward-Compatible Schema Changes
- Carrier Credential Rotation
- Booking Carrier Mapping
- Legacy Gateway Cleanup

## God Nodes (most connected - your core abstractions)
1. `Booking Service` - 13 edges
2. `Pricing Service` - 9 edges
3. `parse()` - 8 edges
4. `Public API Gateway` - 8 edges
5. `Severity-Based Owner Escalation` - 8 edges
6. `inline()` - 7 edges
7. `jobs` - 6 edges
8. `build_table()` - 6 edges
9. `render()` - 6 edges
10. `Concurrent Reserve Double-Booking Incident` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Concurrent Reserve Double-Booking Incident` --references--> `Independent Per-Carrier Rate Limits`  [EXTRACTED]
  postmortems/2026-06-14-double-booking.md → adr/0007-rate-limit-per-carrier.md
- `Incident Classification and Owner-Based Escalation` --references--> `Published On-Call Policy`  [EXTRACTED]
  policies/on-call-policy.md → policies/on-call-policy.pdf
- `Global Rate-Limit 429 Storm` --references--> `Incident Classification and Owner-Based Escalation`  [EXTRACTED]
  postmortems/2026-08-21-gateway-429-storm.md → policies/on-call-policy.md
- `OPS-51 Rewrite On-Call Policy` --references--> `Incident Classification and Owner-Based Escalation`  [EXTRACTED]
  tickets/OPS-51.md → policies/on-call-policy.md
- `Booking PostgreSQL Failover` --references--> `Concurrent Reserve Double-Booking Incident`  [EXTRACTED]
  runbooks/db-failover.md → postmortems/2026-06-14-double-booking.md

## Import Cycles
- 1-file cycle: `scripts/build_pdfs.py -> scripts/build_pdfs.py`

## Hyperedges (group relationships)
- **Safe Shipment Reservation** — adr_0006_idempotent_booking_references_client_reference, postmortems_2026_06_14_double_booking_advisory_lock, postmortems_2026_06_14_double_booking_capacity_hold [EXTRACTED 1.00]
- **ETA Confidence Consumer Rollout** — adr_0008_eta_confidence_scoring_eta_confidence, adr_0001_split_monolith_into_services_api_gateway, adr_0001_split_monolith_into_services_customer_web [EXTRACTED 1.00]
- **Carrier Resilience and Contract Controls** — adr_0007_rate_limit_per_carrier_carrier_rate_limiter, postmortems_2026_06_14_double_booking_capacity_hold, postmortems_2026_03_02_pricing_timeout_atomic_tariff_snapshot [INFERRED 0.75]

## Communities (22 total, 11 thin omitted)

### Community 0 - "PDF Build Pipeline"
Cohesion: 0.12
Nodes (20): pathlib, re, reportlab_lib, reportlab_lib_enums, reportlab_lib_pagesizes, reportlab_lib_styles, reportlab_lib_units, reportlab_platypus (+12 more)

### Community 1 - "ADLC CI Automation"
Cohesion: 0.09
Nodes (21): if, permissions, uses, if, uses, if, uses, jobs (+13 more)

### Community 2 - "API Contract ETA Confidence"
Cohesion: 0.13
Nodes (14): Public API Gateway, Customer Web UI, ETA Confidence Heuristic, BOOK-412 Booking ETA Confidence Response, GW-102: Remove dead legacy/pricing_v1.py, GW-110: Translate upstream 429 to 503 'booking temporarily unavailable', GW-118: Gateway ShipmentOut missing eta_confidence, GW-84: Structured 504 body when pricing times out (+6 more)

### Community 3 - "Tariff and Pricing Operations"
Cohesion: 0.21
Nodes (11): Pricing Service, Atomic Tariff Snapshot Reload, Synchronous Tariff Reload and Thundering Herd, Tariff Refresh Quote Timeout Incident, Safe Pricing Tariff Reload, PRC-211: Reload tariffs into a new snapshot and swap atomically, PRC-214: Alert and log when tariff reload exceeds 5 seconds, PRC-233: Rounding mismatch: fuel surcharge Math.Round vs Money.Round (pricing and web) (+3 more)

### Community 4 - "Carrier Limits and Money"
Cohesion: 0.19
Nodes (10): Half-Away-From-Zero Rounding, CarrierRateLimiter Token Buckets, Shared Global Bucket Failure, Global Rate-Limit 429 Storm, Carrier SLA and Rate Budget, Carrier Onboarding and SLA Budget, Per-Carrier 429 Mitigation Procedure, Published Carrier API Service Levels (+2 more)

### Community 5 - "On-Call Ownership Escalation"
Cohesion: 0.17
Nodes (12): Service-Owner Decision Authority, Severity-Based Owner Escalation, SEV1 and SEV2 Owner Escalation Timers, Published On-Call Policy, Incident Classification and Owner-Based Escalation, Weekly On-Call Handover, OPS-38: Add tariff size and load-time check to carrier onboarding, OPS-44: Postmortem template and blameless review process (+4 more)

### Community 6 - "Booking Service Operations"
Cohesion: 0.20
Nodes (9): Booking Service, Safe Booking Service Restart, BOOK-377: carriers FK missing on JPA entity, BOOK-398: Double booking incident follow-up (advisory lock), BOOK-401: Concurrent reserve test (50 threads, same reference), BOOK-405: Alert on advisory lock waits longer than 2 seconds, BOOK-409: Replace global limiter with per-carrier CarrierRateLimiter, BOOK-412: Add eta_confidence to the /v2/shipments response (+1 more)

### Community 7 - "ADLC Workflow Triggers"
Cohesion: 0.39
Nodes (7): Deterministic Shipment Reference, Transaction-Scoped PostgreSQL Advisory Lock, Carrier Capacity Hold, Concurrent Reserve Read-Check-Write Race, Concurrent Reserve Double-Booking Incident, Booking PostgreSQL Failover, BOOK-398 Advisory Lock for Concurrent Reservations

### Community 8 - "Idempotent Reservation Safety"
Cohesion: 0.29
Nodes (7): on, pull_request, push, schedule, workflow_dispatch, branches, cron

### Community 9 - "Production Change Controls"
Cohesion: 0.50
Nodes (4): Ticketed, Reviewed, Reversible Production Changes, Production Change Management Controls, Service Deployment Rollback, Carrier Credential Rotation

### Community 10 - "Dependency Update Configuration"
Cohesion: 0.50
Nodes (3): github>kestrel-freight/adlc-kit//monitor/renovate-preset.json#v0.1.0, extends, $schema

## Knowledge Gaps
- **55 isolated node(s):** `github>kestrel-freight/adlc-kit//monitor/renovate-preset.json#v0.1.0`, `Kestrel Operations Documentation Governance`, `Kestrel Freight Platform Architecture`, `Architecture Decision Record Catalog`, `Kestrel Freight Domain and Technical Glossary` (+50 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 85 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Booking Service` connect `Booking Service Operations` to `API Contract ETA Confidence`, `Carrier Limits and Money`, `ADLC Workflow Triggers`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **What connects `github>kestrel-freight/adlc-kit//monitor/renovate-preset.json#v0.1.0`, `Kestrel Operations Documentation Governance`, `Kestrel Freight Platform Architecture` to the rest of the system?**
  _55 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `PDF Build Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.11965811965811966 - nodes in this community are weakly interconnected._
- **Why does `Pricing Service` connect `Tariff and Pricing Operations` to `API Contract ETA Confidence`, `Carrier Limits and Money`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Should `ADLC CI Automation` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Why does `Global Rate-Limit 429 Storm` connect `Carrier Limits and Money` to `On-Call Ownership Escalation`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Should `API Contract ETA Confidence` be split into smaller, more focused modules?**
  _Cohesion score 0.13071895424836602 - nodes in this community are weakly interconnected._