#!/bin/bash

# CarbonCompliance Agent Setup for Colleagues
echo "📱 CarbonCompliance Agent Setup"

# Get server IP from user
read -p "Enter your server IP address: " SERVER_IP
read -p "Enter your name (for identification): " USER_NAME

echo "🔗 Connecting to server: $SERVER_IP"
echo "👤 Agent will be identified as: $USER_NAME"

# Pull agent image
echo "📥 Downloading agent..."
docker pull saadhaniftaj/endpoint-agent:latest

# Run agent with user identification
echo "🚀 Starting compliance monitoring..."
docker run --rm \
  --read-only \
  --cap-drop=ALL \
  --user nobody \
  --security-opt no-new-privileges \
  -e API_URL="http://$SERVER_IP:8000" \
  -e DEVICE_NAME="$USER_NAME" \
  saadhaniftaj/endpoint-agent:latest

echo "✅ Agent setup complete!"
echo "📊 Your compliance data is now being monitored"
echo "🌐 View dashboard at: http://$SERVER_IP"
