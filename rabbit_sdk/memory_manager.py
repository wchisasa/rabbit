# Rabbit/rabbit_sdk/memory_manager.py
"""
Manages short-term and long-term memory using SQLite + in-memory cache.
""" 
import sqlite3

class MemoryManager:
    """Handles memory storage and retrieval using SQLite."""
    def __init__(self, db_name="memory.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Creates the memory table if it does not exist."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS memory (
                                session_id TEXT,
                                key TEXT,
                                value TEXT,
                                PRIMARY KEY (session_id, key))''')
        self.conn.commit()

    def save(self, session_id, key, value):
        """Stores a value in memory under a session ID."""
        self.cursor.execute('''INSERT INTO memory (session_id, key, value) 
                               VALUES (?, ?, ?) ON CONFLICT(session_id, key) DO UPDATE SET value = excluded.value''',
                            (session_id, key, value))
        self.conn.commit()

    def get(self, session_id, key):
        """Retrieves a stored value from memory."""
        self.cursor.execute('''SELECT value FROM memory WHERE session_id = ? AND key = ?''', (session_id, key))
        result = self.cursor.fetchone()
        return result[0] if result else None
