#!/bin/bash

# Stop Raycast Focus Tracker
# Kills all raycast-tracker related processes including menu bar app

echo "Stopping Raycast Focus Tracker..."

# Kill all raycast-tracker related processes
pkill -f "raycast-tracker"
pkill -f "focus-tracker.sh" 
pkill -f "log stream.*com.raycast.macos"
pkill -f "menuBar.py"
pkill -f "raycast_focus_tracker"

echo "All Raycast Focus Tracker processes stopped"