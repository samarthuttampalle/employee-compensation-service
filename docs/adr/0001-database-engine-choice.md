# ADR 0001: Database engine choice

- **Status:** Accepted
- **Date:** 2026-07-29
- **Context:** Assignment Part A/B requires a relational store with foreign keys, aggregates, and window functions.

## Decision

Use **Azure SQL Database** in production and **SQL Server** (local Express / Azure SQL Edge) for development.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| Azure SQL / SQL Server | Native Azure + Managed Identity; full T-SQL (`RANK`, `HAVING`, `IDENTITY`); matches brief schema notation | Windows/ODBC driver setup locally |
| PostgreSQL | Excellent window functions; cleaner `NULLS LAST` | More translation from brief's `IDENTITY`-style schema; weaker Azure Functions pairing for this exercise |
| Cosmos DB | Managed Azure | Not relational; poor fit for multi-row aggregates/window reports |
| SQLite | Easy local smoke tests | Not production-representative; weak concurrent write story |

## Rationale

1. The brief's schema (`IDENTITY`, `DECIMAL(12,2)`, SQL Server–flavored DDL) points at SQL Server.
2. Reporting requirements B4–B6 are natural in T-SQL and are written as explicit parameterized SQL in the repository layer.
3. Production secrets can use Key Vault + Managed Identity (and optionally Entra auth to Azure SQL).

## Consequences

- Local development requires ODBC Driver 18 and a SQL Server instance (Express is sufficient).
- Integration tests reset schema via `sql/001`–`003` against the configured connection string.
- Postgres remains a documented alternative if engine portability is needed later; NULL ordering and `TOP`/`LIMIT` would need dialect adjustments.
