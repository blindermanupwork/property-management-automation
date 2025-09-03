#!/bin/bash
# Quick fix for airscripts-api port conflicts

echo "🔍 Checking for processes on port 3002..."
PID=$(sudo ss -tlnp | grep :3002 | grep -o 'pid=[0-9]*' | cut -d'=' -f2)

if [ -n "$PID" ]; then
    echo "❌ Port 3002 is busy (PID: $PID)"
    echo "🔪 Killing process $PID..."
    sudo kill -9 $PID
    sleep 2
fi

echo "🔄 Restarting airscripts-api service..."
sudo systemctl restart airscripts-api

echo "✅ Status:"
sudo systemctl status airscripts-api --no-pager -l