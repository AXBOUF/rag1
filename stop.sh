#!/usr/bin/env bash

echo "== Stopping application"

# Kill backend server (port 8001)
echo "Stopping backend server..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || echo "Backend not running"

# Kill frontend server (npm dev - typically port 5173 or 3000)
echo "Stopping frontend server..."
pkill -f "node.*NODE GLOW LOGIN" 2>/dev/null || echo "Frontend not running"

echo "Application stopped."