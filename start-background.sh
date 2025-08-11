#!/bin/bash
# Simple background launcher for Raycast Focus Tracker

echo "Starting Raycast Focus Tracker in background..."

# Create logs directory
mkdir -p logs

# Start in background with output redirected
nohup raycast-tracker > logs/daemon.log 2>&1 &

echo "Started in background (PID: $!)"
echo "Logs: logs/daemon.log" 
echo "Use 'raycast-tracker-stop' to stop it."