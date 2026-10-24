# Employee Compensation Service

HTTP API for HR tooling to manage employees/departments and run compensation reports. All reads and writes go through **Azure Functions**; **SQL Server / Azure SQL** is the system of record.

This repository implements Parts A (CRUD), B (reporting), and C (production readiness) from the assignment brief.

## Architecture

Four layers: **API → Service → Repository → Database**.

See [docs/architecture.md](docs/architecture.md) for diagrams and layer responsibilities.

```
Azure Functions (Python v2)
  └── Blueprints: employees / departments / reports
        └── Services (business rules)
              └── Repositories (SQLAlchemy Core + parameterized T-SQL)
                    └── SQL Server / Azure SQL
```

## Tech stack

| Concern | Choice |
|---------|--------|
| Runtime | Azure Functions v4, Python 3.11 |
| Database | SQL Server (local) / Azure SQL (prod) |
| Data access | SQLAlchemy 2.0 Core + `pyodbc` |
| Validation | Pydantic v2 |
| Config | `pydantic-settings` + env / `local.settings.json` |
| Tests | pytest (unit, API, integration) |
| IaC | Bicep |
| CI | GitHub Actions |

## Prerequisites

- Python 3.11+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local) (`func`)
- ODBC Driver 18 for SQL Server
- Local **SQL Server Express** (or Azure SQL) with a database named `EmployeeCompensation`
- (Optional) Azure CLI for cloud deploy

> Docker is **not** required. This project uses local SQL Server Express for development.

## Local setup

### 1. Clone and create a virtual environment

```powershell
git clone https://github.com/samarthuttampalle/employee-compensation-service.git
cd employee-compensation-service

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Configure local settings

```powershell
Copy-Item local.settings.json.example local.settings.json
```

Edit `local.settings.json` and set `SQL_CONNECTION_STRING` to your instance, for example:

```text
Driver={ODBC Driver 18 for SQL Server};Server=YOUR_PC\SQLEXPRESS;Database=EmployeeCompensation;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;
```

`local.settings.json` is gitignored. Never commit real connection strings.

### 3. Create schema and seed data

Create an empty database `EmployeeCompensation` in SSMS / Azure Data Studio, then run **in order**:

1. `sql/003_drop_schema.sql` (safe if tables do not exist yet)
2. `sql/001_create_schema.sql`
3. `sql/002_seed_data.sql`

You should have **5 departments** and **10 employees**.

### 4. Start the Functions host

```powershell
.\.venv\Scripts\Activate.ps1
func start
```

Base URL: `http://localhost:7071/api`

Smoke test:

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:7071/api/health"
```

Expected: `"status": "healthy"`.

If requests return **401**, append the function key from `func start` output (`?code=...`) or send header `x-functions-key`.

## Running tests

```powershell
# Fast: unit + API (mocked services / no live SQL required for most)
.\.venv\Scripts\python.exe -m pytest tests\unit tests\api -q

# Integration: requires SQL_CONNECTION_STRING (from env or local.settings.json)
.\.venv\Scripts\python.exe -m pytest tests\integration -q

# Full suite
.\.venv\Scripts\python.exe -m pytest tests -q

# Secrets audit (Part C1)
.\.venv\Scripts\python.exe scripts\check_no_secrets.py

# Assignment acceptance checks (reseeds DB, then verifies A/B/C)
.\.venv\Scripts\python.exe scripts\run_assignment_verification.py
```

## API documentation

- OpenAPI contract: [docs/openapi.yaml](docs/openapi.yaml)
- Design notes: [docs/Employee_Compensation_Service_TDD.md](docs/Employee_Compensation_Service_TDD.md)

View OpenAPI locally with any Swagger UI / Redoc tool that can load the YAML file.

## Endpoints summary

### Health

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness probe |

### Employees (Part A)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/employees` | Create employee (bonus optional) |
| GET | `/api/employees/{employeeId}` | Get by ID (`?applyDefaultBonus=true` for C3) |
| GET | `/api/employees` | List (`departmentId`, `top`, `skip`) |
| PATCH | `/api/employees/{employeeId}` | Partial update |
| DELETE | `/api/employees/{employeeId}` | Delete |

### Departments

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/departments` | Create |
| GET | `/api/departments/{departmentId}` | Get by ID |
| GET | `/api/departments` | List |
| PATCH | `/api/departments/{departmentId}` | Partial update |
| DELETE | `/api/departments/{departmentId}` | Delete (`?force=true` if employees exist) |

### Reports (Part B)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/reports/total-bonus` | B1 — total bonus (NULL as 0) |
| GET | `/api/reports/employees-without-bonus` | B2 — `Bonus IS NULL` |
| GET | `/api/reports/bonus-percentage` | B3 — bonus % of salary |
| GET | `/api/reports/departments-over-average` | B4 — SUM(bonus) > AVG(salary) |
| GET | `/api/reports/bonus-ranking` | B5 — RANK, NULL last |
| GET | `/api/reports/highest-compensation` | B6 — salary vs total compensation |

### Seed expectations (after `002_seed_data.sql`)

| Check | Expected |
|-------|----------|
| B1 `totalBonusPaid` | `102000.00` |
| B2 employee IDs | `2, 4, 8` |
| B6 highest salary employee | ID `9`, also highest total compensation |

## Design decisions

| Decision | Summary | ADR |
|----------|---------|-----|
| Database engine | Azure SQL / SQL Server for T-SQL + Azure MI fit | [docs/adr/0001-database-engine-choice.md](docs/adr/0001-database-engine-choice.md) |
| Default bonus (C3) | **Read-time**, opt-in via `?applyDefaultBonus=true`, never persisted | [docs/adr/0002-default-bonus-read-time-vs-write-time.md](docs/adr/0002-default-bonus-read-time-vs-write-time.md) |

**Why read-time for C3:** writing a default bonus would break B2 (`Bonus IS NULL`), go stale when salary changes, and mix “never awarded” with “earned 5%”. Read-time keeps storage as the source of truth.

## Deployment

- Local: `func start` (this README)
- Cloud: Azure Functions (Linux, Python 3.11), Consumption plan by default
- IaC: see [infra/README.md](infra/README.md) (`infra/main.bicep`)
- Secrets in production: Key Vault reference + Function App managed identity
- CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — secrets lint, ruff, mypy, unit/API tests

## Assumptions

- Single tenant; no Entra ID auth in scope (function-key auth is the floor)
- B3 excludes employees with `Bonus IS NULL`
- Total compensation = `Salary + COALESCE(Bonus, 0)`
- `DepartmentID` on employees is nullable
- Monetary values are `DECIMAL(12,2)` end-to-end (never `float`)

## Known limitations / future work

- Entra ID authentication and RBAC
- Cursor-based pagination for very large lists
- Retry/backoff on transient SQL failures
- App Insights alert rules on error rate
- See TDD §19 for the full deferred list

## Project layout

```text
src/ecs/          # Application (api, services, repositories, domain, schemas, core)
sql/              # DDL + seed + teardown
tests/            # unit / api / integration
scripts/          # secrets audit + assignment verification
infra/            # Bicep (Function App, SQL, Key Vault, App Insights)
docs/             # TDD, ADRs, OpenAPI, architecture
```
