#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set database path
DB_PATH = Path(os.getenv("DB_PATH", "/app/data/reminders.db"))

print(f"Testing database at: {DB_PATH}")
print(f"Parent directory: {DB_PATH.parent}")
print(f"Parent exists: {DB_PATH.parent.exists()}")
print(f"Database exists: {DB_PATH.exists()}")

if DB_PATH.exists():
    print(f"Database size: {DB_PATH.stat().st_size} bytes")
    
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reminders")
    count = cursor.fetchone()[0]
    print(f"Number of reminders: {count}")
    conn.close()
else:
    print("Initializing database...")
    
    # Create parent directory
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            reminder_datetime TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            notified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            user_id TEXT DEFAULT 'default'
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✓ Database initialized successfully")
    print(f"Database size: {DB_PATH.stat().st_size} bytes")
