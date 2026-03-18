#!/bin/bash

# Remote AI-based Threat Modeling Services
# Designed for containerized/Kubernetes deployment

echo "Starting Remote AI Threat Modeling Services..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start Threat Model API (port 8010)
echo "Starting Threat Model API on port 8010..."
uvicorn threat_model_endpoint:app --host 0.0.0.0 --port 8010 &

# Start Mitigation API (port 8000) 
echo "Starting Mitigation API on port 8000..."
uvicorn Mitigation_endpoint_remote:app --host 0.0.0.0 --port 8000 &

echo "Services started!"
echo ""
echo "Threat Model API: http://localhost:8010"
echo "Mitigation API: http://localhost:8000"
echo ""
echo "Health Checks:"
echo "curl http://localhost:8010/health"
echo "curl http://localhost:8000/health"
echo ""
echo "Provider Info:"
echo "curl http://localhost:8010/providers"
echo "curl http://localhost:8000/providers"
echo ""
echo "See CONFIGURATION.md for API usage examples"

wait
