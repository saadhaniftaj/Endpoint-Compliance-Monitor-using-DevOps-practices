#!/bin/bash

# CarbonCompliance Production Deployment Script
echo "🚀 Deploying CarbonCompliance Production System..."

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker pull saadhaniftaj/carboncompliance-backend:latest
docker pull saadhaniftaj/carboncompliance-frontend:latest
docker pull saadhaniftaj/endpoint-agent:latest

# Create network if it doesn't exist
echo "🌐 Creating Docker network..."
docker network create carboncompliance-network 2>/dev/null || true

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker stop carboncompliance-backend carboncompliance-frontend 2>/dev/null || true
docker rm carboncompliance-backend carboncompliance-frontend 2>/dev/null || true

# Start Backend
echo "🔧 Starting CarbonCompliance Backend..."
docker run -d \
  --name carboncompliance-backend \
  --network carboncompliance-network \
  -p 8000:8000 \
  -v carboncompliance-data:/app/data \
  --restart unless-stopped \
  saadhaniftaj/carboncompliance-backend:latest

# Start Frontend
echo "🎨 Starting CarbonCompliance Frontend..."
docker run -d \
  --name carboncompliance-frontend \
  --network carboncompliance-network \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  saadhaniftaj/carboncompliance-frontend:latest

echo "✅ CarbonCompliance System Deployed Successfully!"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard: http://localhost"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "📱 To run an agent on any endpoint:"
echo "   docker run --rm -e API_URL=http://your-backend-ip:8000 saadhaniftaj/endpoint-agent:latest"
