targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short name prefix for resources (letters/numbers only, lowercase).')
param namePrefix string = 'ecs'

@description('Environment label (dev/staging/prod).')
param environmentName string = 'dev'

@description('Function App hosting plan SKU. Use Y1 for Consumption, EP1 for Premium.')
param functionAppSku string = 'Y1'

@description('SQL administrator login.')
param sqlAdministratorLogin string

@secure()
@description('SQL administrator password.')
param sqlAdministratorLoginPassword string

@secure()
@description('Full SQL ODBC connection string stored in Key Vault for the Function App.')
param sqlConnectionString string

@description('Optional Application Insights sampling percentage.')
param appInsightsSamplingPercentage int = 100

var uniqueSuffix = uniqueString(resourceGroup().id, namePrefix, environmentName)
var storageAccountName = take('st${namePrefix}${uniqueSuffix}', 24)
var functionAppName = 'func-${namePrefix}-${environmentName}-${take(uniqueSuffix, 6)}'
var appServicePlanName = 'asp-${namePrefix}-${environmentName}'
var sqlServerName = 'sql-${namePrefix}-${environmentName}-${take(uniqueSuffix, 6)}'
var keyVaultName = take('kv${namePrefix}${take(uniqueSuffix, 10)}', 24)
var appInsightsName = 'appi-${namePrefix}-${environmentName}'
var logAnalyticsName = 'log-${namePrefix}-${environmentName}'
var tags = {
  project: 'employee-compensation-service'
  environment: environmentName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: functionAppSku
  }
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
  }
}

module sqlModule 'modules/sql.bicep' = {
  name: 'sql'
  params: {
    location: location
    sqlServerName: sqlServerName
    sqlDatabaseName: 'EmployeeCompensation'
    sqlAdministratorLogin: sqlAdministratorLogin
    sqlAdministratorLoginPassword: sqlAdministratorLoginPassword
    tags: tags
  }
}

module keyVaultModule 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    keyVaultName: keyVaultName
    functionAppPrincipalId: functionApp.identity.principalId
    sqlConnectionString: sqlConnectionString
    tags: tags
  }
}

resource functionAppSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: {
    FUNCTIONS_EXTENSION_VERSION: '~4'
    FUNCTIONS_WORKER_RUNTIME: 'python'
    AzureWebJobsStorage: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
    APPINSIGHTS_SAMPLING_PERCENTAGE: string(appInsightsSamplingPercentage)
    DEFAULT_BONUS_RATE: '0.05'
    LOG_LEVEL: 'INFO'
    MAX_PAGE_SIZE: '200'
    SQL_CONNECTION_STRING: keyVaultModule.outputs.sqlConnectionAppSettingReference
  }
}

output functionAppName string = functionApp.name
output functionAppHostname string = functionApp.properties.defaultHostName
output sqlServerFqdn string = sqlModule.outputs.sqlServerFqdn
output keyVaultUri string = keyVaultModule.outputs.keyVaultUri
output applicationInsightsName string = appInsights.name
