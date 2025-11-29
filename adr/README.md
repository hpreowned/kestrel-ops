# Architecture Decision Records

ADRs are written in MADR style (Context, Decision, Consequences, plus Status, Date and
Deciders). They are reviewed by `@kestrel/architecture-guild` (see ADR-0009 and
`CODEOWNERS`). An accepted ADR is never rewritten; if a decision changes, add a new ADR
and mark the old one "Superseded by". Small clarifications are recorded in a
"Last amended" line.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-split-monolith-into-services.md) | Split the booking monolith into services | Accepted |
| [0002](0002-java-spring-for-booking.md) | Java 21 and Spring Boot for booking | Accepted |
| [0003](0003-dotnet-for-pricing.md) | .NET 8 for pricing | Accepted |
| [0004](0004-python-fastapi-gateway.md) | Python 3.12 and FastAPI for the gateway | Accepted |
| [0005](0005-money-as-decimal-minor-units.md) | Money is decimal, minor units, half away from zero | Accepted |
| [0006](0006-idempotent-booking-references.md) | Idempotent booking references | Accepted |
| [0007](0007-rate-limit-per-carrier.md) | Rate limit carrier calls per carrier | Accepted |
| [0008](0008-eta-confidence-scoring.md) | ETA confidence scoring | Accepted |
| [0009](0009-team-boundaries-and-codeowners.md) | Team boundaries and CODEOWNERS | Accepted |

## Writing a new ADR

1. Copy the header block of the most recent ADR and take the next number.
2. Use a lowercase, hyphenated slug that states the decision, not the topic.
3. Open a PR; the architecture guild reviews on Thursdays. Name every affected team.
4. Reference ADR numbers from code with a `WHY:` comment when the code would otherwise
   look arbitrary.
