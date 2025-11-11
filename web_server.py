import os
import subprocess
import logging
from flask import Flask, jsonify, render_template_string
from datetime import datetime
import sqlite3
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("web_server")

app = Flask(__name__)
DB_PATH = Path(os.getenv("DB_PATH", "/app/data/reminders.db"))

# HTML template for status page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Xiaozhi Reminder Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        h1 { 
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .status {
            background: #f7fafc;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .status-item:last-child { border-bottom: none; }
        .label { 
            color: #4a5568;
            font-weight: 600;
        }
        .value {
            color: #2d3748;
            font-weight: 500;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-success { background: #c6f6d5; color: #22543d; }
        .badge-warning { background: #feebc8; color: #7c2d12; }
        .badge-info { background: #bee3f8; color: #2c5282; }
        .footer {
            text-align: center;
            color: #718096;
            margin-top: 30px;
            font-size: 0.9em;
        }
        .emoji { font-size: 1.5em; margin-right: 8px; }
        .refresh-note {
            background: #edf2f7;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #4a5568;
        }
    </style>
    <script>
        setTimeout(() => location.reload(), 30000);
    </script>
</head>
<body>
    <div class="container">
        <h1><span class="emoji">⏰</span>Xiaozhi Reminder Server</h1>
        <p class="subtitle">MCP Server Status Dashboard</p>
        
        <div class="status">
            <div class="status-item">
                <span class="label">Server Status</span>
                <span class="value"><span class="badge badge-success">{{ status }}</span></span>
            </div>
            <div class="status-item">
                <span class="label">Uptime</span>
                <span class="value">{{ uptime }}</span>
            </div>
            <div class="status-item">
                <span class="label">Total Reminders</span>
                <span class="value">{{ stats.total }}</span>
            </div>
            <div class="status-item">
                <span class="label">Pending</span>
                <span class="value"><span class="badge badge-info">{{ stats.pending }}</span></span>
            </div>
            <div class="status-item">
                <span class="label">Overdue</span>
                <span class="value"><span class="badge badge-warning">{{ stats.overdue }}</span></span>
            </div>
            <div class="status-item">
                <span class="label">Completed</span>
                <span class="value"><span class="badge badge-success">{{ stats.completed }}</span></span>
            </div>
            <div class="status-item">
                <span class="label">Last Check</span>
                <span class="value">{{ last_check }}</span>
            </div>
        </div>
        
        <div class="refresh-note">
            📡 This page auto-refreshes every 30 seconds<br>
            🔗 Connected to Xiaozhi AI via WebSocket<br>
            💾 Database: {{ db_status }}
        </div>
        
        <div class="footer">
            <p>Xiaozhi Reminder MCP Server v1.0</p>
            <p>Made with ❤️ for Xiaozhi AI</p>
        </div>
    </div>
</body>
</html>
"""

start_time = datetime.now()

def get_db_stats():
    """Get reminder statistics from database"""
    try:
        if not DB_PATH.exists():
            return {"total": 0, "pending": 0, "overdue": 0, "completed": 0}
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reminders")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reminders WHERE completed = 0")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reminders WHERE completed = 1")
        completed = cursor.fetchone()[0]
        
        now = datetime.now()
        cursor.execute("SELECT COUNT(*) FROM reminders WHERE completed = 0 AND reminder_datetime < ?", (now.isoformat(),))
        overdue = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "overdue": overdue
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"total": 0, "pending": 0, "overdue": 0, "completed": 0}


@app.route('/')
def index():
    """Status dashboard page"""
    stats = get_db_stats()
    uptime = datetime.now() - start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    
    db_status = "Connected" if DB_PATH.exists() else "Initializing"
    
    return render_template_string(
        HTML_TEMPLATE,
        status="Running",
        uptime=f"{hours}h {minutes}m",
        stats=stats,
        last_check=datetime.now().strftime("%H:%M:%S"),
        db_status=db_status
    )


@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    stats = get_db_stats()
    return jsonify({
        "status": "healthy",
        "uptime_seconds": int((datetime.now() - start_time).total_seconds()),
        "database": "connected" if DB_PATH.exists() else "initializing",
        "stats": stats
    })


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = get_db_stats()
    return jsonify({
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    
    logger.info("=" * 60)
    logger.info("Starting Xiaozhi Reminder Web Server")
    logger.info("=" * 60)
    logger.info(f"Port: {port}")
    logger.info(f"Database: {DB_PATH}")
    logger.info("=" * 60)
    
    # Run Flask server
    app.run(host='0.0.0.0', port=port, debug=False)
