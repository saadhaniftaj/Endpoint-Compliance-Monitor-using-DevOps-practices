#!/bin/bash

# CarbonCompliance Agent Deployment Script
echo "�� Deploying CarbonCompliance Agent..."

# Default values
API_URL=${API_URL:-"http://localhost:8000"}
AGENT_TOKEN=${AGENT_TOKEN:-""}

echo "🔗 Backend URL: $API_URL"
echo "🔑 Agent Token: ${AGENT_TOKEN:-"None"}"

# Pull latest agent image
echo "📥 Pulling latest agent image..."
docker pull saadhaniftaj/endpoint-agent:latest

# Run agent with security hardening
echo "🚀 Starting CarbonCompliance Agent..."
docker run --rm \
  --read-only \
  --cap-drop=ALL \
  --user nobody \
  --security-opt no-new-privileges \
  -e API_URL="$API_URL" \
  -e AGENT_TOKEN="$AGENT_TOKEN" \
  saadhaniftaj/endpoint-agent:latest

echo "✅ Agent deployment completed!"
