@description('Specify the name of the Azure Managed Redis to create.')
param redisCacheName string = 'redisCache-${uniqueString(resourceGroup().id)}'

@description('The SKU of the Azure Managed Redis to create.')
param redisSku string = 'Balanced_B5'

@description('The port of the Azure Managed Redis to create.')
param redisPort int = 10000

@description('That is the name of the Azure OpenAI Service to create.')
param aoaiName string = 'aoai-${uniqueString(resourceGroup().id)}'

@description('Location of all resources')
param location string = resourceGroup().location

@allowed([
  'S0'
])
param aoaiSku string = 'S0'

var models = [
  {
    name: 'text-embedding-3-large'
    version: '1'
    capacity: 250
    deploymentType: 'GlobalStandard'
    format: 'OpenAI'
  }
  {
    name: 'gpt-4o-mini'
    version: '2024-07-18'
    capacity: 250
    deploymentType: 'GlobalStandard'
    format: 'OpenAI'
  }
]

resource redisEnterprise 'Microsoft.Cache/redisEnterprise@2024-10-01' = {
  name: redisCacheName
  location: location
  sku: {
    name: redisSku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    minimumTlsVersion: '1.2'    
  }
}

resource redisEnterpriseDatabase 'Microsoft.Cache/redisEnterprise/databases@2024-10-01' = {
  name: 'default'
  parent: redisEnterprise
  properties:{
    clientProtocol: 'Encrypted'
    port: redisPort
    clusteringPolicy: 'EnterpriseCluster'
    evictionPolicy: 'NoEviction'
    persistence:{
      aofEnabled: false 
      rdbEnabled: false
    }
    modules: [
      {
        name: 'RediSearch'
      }
    ]
  }
}

resource openAIService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: aoaiName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: aoaiSku
  }
  kind: 'OpenAI'
  properties: {
    publicNetworkAccess: 'Enabled'
  }
}

@batchSize(1)
resource azopenaideployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [for model in models: {
  parent: openAIService
  name: model.name
  properties: {
      model: {
          format: model.format
          name: model.name
          version: model.version
      }
  }
  sku: {
    name: model.deploymentType
    capacity: model.capacity
  }
}]

output redisCacheName string = redisEnterprise.name
output redisCacheEndpoint string = redisEnterprise.properties.hostName
output redisCachePort int = redisEnterpriseDatabase.properties.port
output openAIServiceEndpoint string = openAIService.properties.endpoint
output openAIServiceName string = openAIService.name
