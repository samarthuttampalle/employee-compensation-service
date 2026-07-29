# Infrastructure (Bicep)

Provisions the Azure footprint for the Employee Compensation Service:

- Storage account (Functions runtime)
- Linux Consumption (or Premium) Function App with **system-assigned managed identity**
- Azure SQL Server + `EmployeeCompensation` database
- Key Vault secret for `SQL_CONNECTION_STRING` (App Setting Key Vault reference)
- Log Analytics + Application Insights

## Layout

```text
infra/
  main.bicep
  main.parameters.json
  modules/
    sql.bicep
    keyvault.bicep
```

## Prerequisites

- Azure CLI logged in (`az login`)
- A resource group
- A strong SQL admin password and a ready ODBC connection string for Key Vault

## Deploy

```powershell
az group create --name rg-ecs-dev --location eastus

az deployment group create `
  --resource-group rg-ecs-dev `
  --template-file infra/main.bicep `
  --parameters infra/main.parameters.json `
  --parameters sqlAdministratorLoginPassword="YOUR_SECURE_PASSWORD" `
             sqlConnectionString="Driver={ODBC Driver 18 for SQL Server};Server=tcp:<fqdn>,1433;Database=EmployeeCompensation;Uid=ecs_admin;Pwd=YOUR_SECURE_PASSWORD;Encrypt=yes;TrustServerCertificate=no;"
```

After SQL is up, apply `sql/001_create_schema.sql` and `sql/002_seed_data.sql` (via SSMS, Azure Data Studio, or `sqlcmd`).

Deploy Function App code:

```powershell
func azure functionapp publish <functionAppName> --python
```

## Notes

- Prefer Entra ID Managed Identity auth to Azure SQL in production when available; Key Vault–referenced SQL auth is the documented fallback.
- Switch to Premium with parameter `functionAppSku=EP1`.
- Do not commit real passwords or connection strings; `main.parameters.json` uses placeholders only.
