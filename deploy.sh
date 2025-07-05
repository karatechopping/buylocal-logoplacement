#!/bin/bash
# Deployment script for Logo Placement Analyzer

set -e  # Exit on any error

# Configuration
DEPLOY_USER=$(whoami)
DEPLOY_PATH="/opt/buylocal-logoplacement"
SERVICE_NAME="logo-analyzer"

echo "🚀 Starting deployment..."

# Stop service if running
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Create deployment directory
sudo mkdir -p $DEPLOY_PATH
sudo chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH

# Copy application files
echo "📦 Copying application files..."
cp -r . $DEPLOY_PATH/
cd $DEPLOY_PATH

# Set up virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install systemd service
echo "⚙️  Installing systemd service..."
sudo cp deploy/logo-analyzer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Start service
echo "🎯 Starting service..."
sudo systemctl start $SERVICE_NAME

# Check status
echo "📊 Service status:"
sudo systemctl status $SERVICE_NAME --no-pager

echo "✅ Deployment complete!"
echo "🌐 Service running on http://$(curl -s ifconfig.me):5001"