# Architecture

## Layered design

```mermaid
flowchart TB
  Client[HTTP Client / HR tooling]
  API[API layer<br/>Azure Functions blueprints]
  SVC[Service layer<br/>business rules]
  REPO[Repository layer<br/>SQLAlchemy Core + T-SQL]
  DB[(SQL Server / Azure SQL)]

  Client --> API
  API --> SVC
  SVC --> REPO
  REPO --> DB
```

| Layer | Responsibility | Location |
|-------|----------------|----------|
| API | Routing, parsing, status codes, error envelope | `src/ecs/api/` |
| Service | FK checks, delete guards, default-bonus policy, B6 comparison | `src/ecs/services/` |
| Repository | Parameterized CRUD + reporting SQL | `src/ecs/repositories/` |
| Domain / schemas | Internal types vs wire contracts | `src/ecs/domain/`, `src/ecs/schemas/` |
| Core | Config, DB engine, exceptions, logging, secrets audit | `src/ecs/core/` |

Dependency rule: **inward only**. Repositories never import API types. Domain has no framework dependencies.

## Composition root

`src/ecs/function_app.py` builds one SQLAlchemy `Engine` per process, constructs repositories and services, initializes blueprints, and registers them on the `FunctionApp`. Root `function_app.py` re-exports `app` for the Functions host.

## Error flow

```mermaid
flowchart LR
  H[Route handler] -->|raises| D[Domain exceptions]
  D --> M[handle_errors decorator]
  M -->|400/404/409/503/500| E[Standard error envelope]
  M --> L[Structured logs + correlationId]
```

## Reporting SQL

CRUD uses SQLAlchemy Core expression builders. Part B reports use **hand-written parameterized T-SQL** (`sqlalchemy.text`) so `HAVING`, `RANK()`, and explicit NULL ordering remain inspectable and testable.
