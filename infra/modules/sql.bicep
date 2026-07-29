@description('Azure region for SQL resources.')
param location string = resourceGroup().location

@description('SQL server name (globally unique).')
param sqlServerName string

@description('SQL database name.')
param sqlDatabaseName string = 'EmployeeCompensation'

@description('SQL admin login name.')
param sqlAdministratorLogin string

@secure()
@description('SQL admin password (prefer Entra-only auth in production when possible).')
param sqlAdministratorLoginPassword string

@description('Optional tags.')
param tags object = {}

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: sqlServerName
  location: location
  tags: tags
  properties: {
    administratorLogin: sqlAdministratorLogin
    administratorLoginPassword: sqlAdministratorLoginPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
  }
}

resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAllWindowsAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

@description('Fully qualified SQL server hostname.')
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName

@description('SQL database name.')
output sqlDatabaseNameOut string = sqlDatabase.name

@description('ODBC connection string template using SQL auth (prefer Managed Identity in production).')
output sqlConnectionStringTemplate string = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${sqlDatabase.name};Uid=${sqlAdministratorLogin};Pwd=<password>;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
