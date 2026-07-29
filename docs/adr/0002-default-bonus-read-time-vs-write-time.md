# ADR 0002: Default bonus — read-time vs write-time

- **Status:** Accepted
- **Date:** 2026-07-29
- **Context:** Part C3 asks whether employees without a bonus should receive a default of 5% of salary, and whether that should be computed at read time or written to storage.

## Decision

Implement the default bonus as a **read-time, opt-in** computation:

- Query flag: `GET /api/employees/{id}?applyDefaultBonus=true`
- When stored `Bonus IS NULL`, response includes:
  - `bonus: null` (unchanged storage)
  - `effectiveBonus: salary * DEFAULT_BONUS_RATE`
  - `bonusIsDefaulted: true`
- Rate comes from config (`DEFAULT_BONUS_RATE`, default `0.05`)
- **Never persisted** by this feature

## Options considered

| Criterion | Read-time (chosen) | Write-time (rejected) |
|-----------|--------------------|------------------------|
| B2 correctness | Unaffected — `Bonus IS NULL` remains true | Breaks B2 unless an extra “is default” flag is added |
| Staleness | Always recomputed from current salary | Goes stale when salary changes |
| Auditability | No silent mutation of compensation data on read | Persists a number that looks like an awarded bonus |
| Config change | Instant for future reads | Requires backfill |

## Rationale

B2 exists specifically to identify employees who **never received** a bonus. Persisting a synthetic 5% value would conflate “no award” with “earned default,” unless the schema grew a second column. Read-time keeps a single source of truth in storage and makes the policy reversible via configuration.

## Consequences

- Clients that need a display default must pass `applyDefaultBonus=true`.
- Reporting endpoints (B1–B6) intentionally ignore the default policy and operate on stored values only.
- Documented in TDD §7.6 and covered by service/API tests.
