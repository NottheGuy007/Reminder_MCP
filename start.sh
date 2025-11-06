#!/bin/bash

echo "=================================================="
echo "Starting Xiaozhi Reminder Server on Render"
echo "=================================================="

# Create data directory if it doesn't exist
mkdir -p /app/data

# Set database path
export DB_PATH=/app/data/reminders.db

echo "Database path: $DB_PATH"

# Initialize database by running reminder_server.py once
echo "Initializing database..."
timeout 5 python reminder_server.py || true

# Check if database was created
if [ -f "$DB_PATH" ]; then
    echo "✓ Database initialized successfully"
    ls -lh "$DB_PATH"
else
    echo "✗ Warning: Database not found, will be created on first use"
fi

echo "=================================================="
echo "Starting MCP Pipe Server..."
echo "=================================================="

# Start MCP server in background
python mcp_pipe.py &
MCP_PID=$!

echo "MCP Server started with PID: $MCP_PID"

# Wait a bit for MCP server to initialize
sleep 3

echo "=================================================="
echo "Starting Reminder Notifier..."
echo "=================================================="

# Start notifier in foreground (this keeps the container running)
python reminder_notifier.py

# If notifier exits, stop MCP server too
echo "Notifier stopped, shutting down..."
kill $MCP_PID 2>/dev/null || true
wait
