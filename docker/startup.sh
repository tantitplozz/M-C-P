#!/bin/bash
# GOD-TIER AUTOBUY STACK - Production Startup Script

set -e

echo "🚀 Starting GOD-TIER AUTOBUY STACK..."

# Create directories
mkdir -p /app/data /app/logs /app/config

# Start Virtual Display (for headless browser automation)
echo "🖥️  Starting Virtual Display..."
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Start VNC Server (for remote browser viewing)
echo "🔗 Starting VNC Server..."
x11vnc -display :99 -nopw -listen localhost -xkb -ncache 10 -ncache_cr -forever &

# Start Redis if not running
if ! pgrep redis-server >/dev/null; then
    echo "🔴 Starting Redis..."
    redis-server --daemonize yes --port 6379
fi

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! redis-cli ping >/dev/null 2>&1; do
    sleep 1
done
echo "✅ Redis is ready!"

# Initialize database
echo "🗃️  Initializing database..."
python -c "
import sqlite3
import os

os.makedirs('/app/data', exist_ok=True)
conn = sqlite3.connect('/app/data/autobuy.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS results (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        result TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
''')

conn.commit()
conn.close()
print('Database initialized successfully!')
"

# Start Prometheus Node Exporter
echo "📊 Starting Prometheus Node Exporter..."
python -c "
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import time
import threading

# Create metrics
REQUEST_COUNT = Counter('autobuy_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('autobuy_request_duration_seconds', 'Request latency')
ACTIVE_TASKS = Gauge('autobuy_active_tasks', 'Active tasks')

# Start metrics server
start_http_server(8000)
print('Metrics server started on port 8000')
" &

# Check if running in worker mode
if [ "$WORKER_MODE" = "true" ]; then
    echo "👷 Starting Worker Mode (ID: $WORKER_ID)..."
    python -m src.worker.worker_node --worker-id "$WORKER_ID"
else
    echo "🎛️  Starting Main Orchestrator..."

    # Start background services
    echo "🔧 Starting Background Services..."
    python -c "
import asyncio
import sys
sys.path.append('/app')

from src.monitoring.health_monitor import HealthMonitor
from src.monitoring.metrics_collector import MetricsCollector

async def start_services():
    health_monitor = HealthMonitor()
    metrics_collector = MetricsCollector()

    await asyncio.gather(
        health_monitor.start(),
        metrics_collector.start()
    )

asyncio.run(start_services())
" &

    # Start the main application
    echo "🚀 Starting Main Application..."
    cd /app && python src/core/orchestrator.py --start
fi
