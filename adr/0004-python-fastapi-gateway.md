# ADR-0004: Python 3.12 and FastAPI for the gateway

- Status: Accepted
- Date: 2025-10-13
- Last amended: 2026-10-06 (GW-118 and GW-110 references added)
- Deciders: @kestrel/platform-team, @kestrel/architecture-guild

## Context

The gateway is the only service browsers reach. It authenticates callers, forwards to
booking and pricing, and translates upstream failures into stable public responses. It
holds no business rules and should be cheap to change. Platform-team engineers are
Python-first (tooling, infra automation), and the gateway benefits from typed request and
response models that double as the public contract.

## Decision

Implement the gateway in **Python 3.12** with **FastAPI**, **httpx** for upstream calls,
**pydantic-settings** for configuration and **pytest** for tests (`pytest -q`). Package
name `gateway`. Public routes:

- `POST /api/shipments`, `GET /api/shipments/{id}`, `POST /api/shipments/{id}/reserve`
- `POST /api/quote`
- `GET /api/carriers`

Configuration via environment: `BOOKING_BASE_URL`, `PRICING_BASE_URL`,
`KESTREL_FEATURE_MULTI_CARRIER_QUOTES`, `GATEWAY_TIMEOUT_SECONDS`.

Response models (for example `ShipmentOut` in `gateway/models.py`) are declared explicitly
and are **not** pass-through. Anything an upstream returns that is not in the model is
dropped.

## Consequences

- Positive: the public contract is explicit and reviewable in one file.
- Negative: because models are explicit, a new upstream field is silently dropped until
  the gateway model is updated. This is the mechanism behind GW-118 (`eta_confidence`).
  ADR-0008 records the rollout order that avoids it.
- Positive: error translation lives in one place. The 429 to 503 mapping introduced after
  the 2026-08-21 incident is an example (GW-110).
- Negative: Python's GIL caps per-process throughput; we scale horizontally and keep
  handlers async and I/O only.
