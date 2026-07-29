@description('Azure region for the Key Vault resource.')
param location string = resourceGroup().location

@description('Key Vault name (3-24 alphanumeric characters).')
param keyVaultName string

@description('Principal ID of the Function App system-assigned managed identity.')
param functionAppPrincipalId string

@description('Optional tags applied to the Key Vault.')
param tags object = {}

@secure()
@description('SQL connection string stored as a Key Vault secret for App Settings reference.')
param sqlConnectionString string

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: functionAppPrincipalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
    enabledForDeployment: false
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    enableRbacAuthorization: false
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

resource sqlConnectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'SqlConnectionString'
  properties: {
    value: sqlConnectionString
  }
}

@description('Key Vault URI used for App Settings Key Vault references.')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Secret URI for SQL_CONNECTION_STRING Key Vault reference.')
output sqlConnectionSecretUri string = sqlConnectionSecret.properties.secretUriWithVersion

@description('App Setting value format for SQL_CONNECTION_STRING.')
output sqlConnectionAppSettingReference string = '@Microsoft.KeyVault(SecretUri=${sqlConnectionSecret.properties.secretUriWithVersion})'
