#!/usr/bin/env bash
set -e

echo "== Starting application"

# Start backend server in background
echo "Starting backend server on port 8001..."
uvicorn version3.api:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Start frontend server in background
echo "Starting frontend server in NODE GLOW LOGIN..."
cd "Node Glow Login" 
npm run dev &
FRONTEND_PID=$!

# Handle cleanup on exit (Ctrl+C)
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

echo "Application started. Press Ctrl+C to stop."
wait