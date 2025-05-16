#!/bin/bash

openAIServiceEndpoint=$(az deployment group show -g movie-chat -n movie-chat --query "properties.outputs.openAIServiceEndpoint.value" -o tsv)
openAIServiceName=$(az deployment group show -g movie-chat -n movie-chat --query "properties.outputs.openAIServiceName.value" -o tsv)
openAIApiKey=$(az cognitiveservices account keys list --name $openAIServiceName --resource-group movie-chat --query key1 -o tsv)
redisCacheEndpoint=$(az deployment group show -g movie-chat -n movie-chat --query "properties.outputs.redisCacheEndpoint.value" -o tsv)
redisCacheName=$(az deployment group show -g movie-chat -n movie-chat --query "properties.outputs.redisCacheName.value" -o tsv)
redisPassword="<manually-set-password>"

echo "OpenAI Service Endpoint: $openAIServiceEndpoint"
echo "Redis Cache Endpoint: $redisCacheEndpoint"
echo "Redis Cache Name: $redisCacheName"
echo "Redis Cache Password: *************"

cat <<EOF > .env
API_KEY=$openAIApiKey
RESOURCE_ENDPOINT=$openAIServiceEndpoint
DEPLOYMENT_NAME=text-embedding-3-large
MODEL_NAME=text-embedding-3-large
REDIS_ENDPOINT=$redisCacheEndpoint:10000
REDIS_PASSWORD=$redisPassword
EOF
