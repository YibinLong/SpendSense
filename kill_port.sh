#!/bin/bash
# Script to kill processes using a specific port
# Usage: ./kill_port.sh [PORT]
# Default port: 8000

PORT=${1:-8000}

echo "🔍 Checking what's using port $PORT..."

# Find process using the port
PID=$(lsof -ti:$PORT)

if [ -z "$PID" ]; then
    echo "✅ Port $PORT is free - nothing to kill"
    exit 0
fi

echo "📋 Found process(es) using port $PORT:"
lsof -i:$PORT

echo ""
echo "💀 Killing process(es): $PID"
kill -9 $PID

# Wait a moment
sleep 1

# Verify
STILL_RUNNING=$(lsof -ti:$PORT)
if [ -z "$STILL_RUNNING" ]; then
    echo "✅ Port $PORT is now free!"
else
    echo "⚠️  Warning: Port $PORT still in use by PID: $STILL_RUNNING"
    echo "Try running with sudo: sudo ./kill_port.sh $PORT"
fi


