#!/bin/bash

# CarbonCompliance Unraid Server Deployment
echo "🏠 Setting up CarbonCompliance on Unraid Server..."

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "🌐 Server IP: $SERVER_IP"

# Pull latest images
echo "📥 Pulling latest images..."
docker pull saadhaniftaj/carboncompliance-backend:latest
docker pull saadhaniftaj/carboncompliance-frontend:latest

# Create network
docker network create carboncompliance-network 2>/dev/null || true

# Stop existing containers
docker stop carboncompliance-backend carboncompliance-frontend 2>/dev/null || true
docker rm carboncompliance-backend carboncompliance-frontend 2>/dev/null || true

# Start Backend (accessible from network)
echo "🔧 Starting Backend on port 8000..."
docker run -d \
  --name carboncompliance-backend \
  --network carboncompliance-network \
  -p 8000:8000 \
  -v carboncompliance-data:/app/data \
  --restart unless-stopped \
  saadhaniftaj/carboncompliance-backend:latest

# Start Frontend (accessible from network)
echo "🎨 Starting Frontend on port 80..."
docker run -d \
  --name carboncompliance-frontend \
  --network carboncompliance-network \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  saadhaniftaj/carboncompliance-frontend:latest

echo "✅ CarbonCompliance deployed on Unraid Server!"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard: http://$SERVER_IP"
echo "   API: http://$SERVER_IP:8000"
echo "   Health Check: http://$SERVER_IP:8000/health"
echo ""
echo "📱 Share this with your colleagues:"
echo "   Backend URL: http://$SERVER_IP:8000"
echo ""
echo "🔑 Optional: Create an access token for security"
