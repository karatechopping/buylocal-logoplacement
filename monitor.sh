#!/bin/bash
# Simple service monitor script

SERVICE_NAME="logo-analyzer"

# Check if service is running
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): $SERVICE_NAME is down, restarting..."
    systemctl restart $SERVICE_NAME
    
    # Wait a moment and check if it started successfully
    sleep 5
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): $SERVICE_NAME restarted successfully"
    else
        echo "$(date): Failed to restart $SERVICE_NAME"
    fi
else
    echo "$(date): $SERVICE_NAME is running"
fi