# Rabbit/rabbit_sdk/memory_manager.py

"""
Manages short-term and long-term memory using SQLite + in-memory cache.
Provides efficient storage and retrieval of agent's interactions and data. 
"""

import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryManager:
    """Handles memory storage and retrieval using SQLite and in-memory cache."""
    
    def __init__(self, db_name: str = "rabbit_memory.db"):
        """
        Initialize the memory manager.
        
        Args:
            db_name (str): Name of the SQLite database file to use
        """
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.in_memory_cache = {}
        self._create_tables()
        
    def _create_tables(self):
        """Creates the required tables if they do not exist."""
        # Main memory table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                session_id TEXT,
                key TEXT,
                value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, key)
            )
        ''')
        
        # Table for task history
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                task TEXT,
                urls TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for named entities extracted during tasks
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                entity_type TEXT,
                entity_value TEXT,
                source_url TEXT,
                context TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        logger.debug("Database tables created")

    def save(self, session_id: str, key: str, value: Union[str, dict, list]):
        """
        Stores a value in memory under a session ID.
        
        Args:
            session_id (str): Unique session identifier
            key (str): Memory item key
            value (str|dict|list): Value to store (will be converted to JSON if not a string)
        """
        try:
            # Convert complex objects to JSON string
            if not isinstance(value, str):
                value = json.dumps(value)
                
            # Store in SQLite
            self.cursor.execute('''
                INSERT INTO memory (session_id, key, value) 
                VALUES (?, ?, ?) 
                ON CONFLICT(session_id, key) 
                DO UPDATE SET value = excluded.value, timestamp = CURRENT_TIMESTAMP
            ''', (session_id, key, value))
            self.conn.commit()
            
            # Update in-memory cache
            if session_id not in self.in_memory_cache:
                self.in_memory_cache[session_id] = {}
            self.in_memory_cache[session_id][key] = value
            
            logger.debug(f"Saved memory: {session_id}:{key}")
        except Exception as e:
            logger.error(f"Error saving to memory: {str(e)}")

    def get(self, session_id: str, key: str) -> Optional[Any]:
        """
        Retrieves a stored value from memory.
        
        Args:
            session_id (str): Session identifier
            key (str): Memory item key
            
        Returns:
            Any: The stored value or None if not found
        """
        try:
            # Check in-memory cache first
            if session_id in self.in_memory_cache and key in self.in_memory_cache[session_id]:
                return self.in_memory_cache[session_id][key]
            
            # Retrieve from SQLite
            self.cursor.execute('''
                SELECT value FROM memory 
                WHERE session_id = ? AND key = ?
            ''', (session_id, key))
            result = self.cursor.fetchone()
            
            if result:
                # Try to parse as JSON, if it fails return as string
                try:
                    parsed_value = json.loads(result[0])
                    
                    # Update cache
                    if session_id not in self.in_memory_cache:
                        self.in_memory_cache[session_id] = {}
                    self.in_memory_cache[session_id][key] = parsed_value
                    
                    return parsed_value
                except json.JSONDecodeError:
                    # Update cache with string value
                    if session_id not in self.in_memory_cache:
                        self.in_memory_cache[session_id] = {}
                    self.in_memory_cache[session_id][key] = result[0]
                    
                    return result[0]
            return None
        except Exception as e:
            logger.error(f"Error retrieving from memory: {str(e)}")
            return None

    def get_all_for_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves all memory items for a session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            dict: Dictionary of all memory items for the session
        """
        try:
            self.cursor.execute('''
                SELECT key, value FROM memory 
                WHERE session_id = ?
                ORDER BY timestamp DESC
            ''', (session_id,))
            results = self.cursor.fetchall()
            
            memory_items = {}
            for key, value in results:
                try:
                    memory_items[key] = json.loads(value)
                except json.JSONDecodeError:
                    memory_items[key] = value
                    
            return memory_items
        except Exception as e:
            logger.error(f"Error retrieving session memory: {str(e)}")
            return {}

    def save_task_result(self, session_id: str, task: str, urls: List[str], result: Dict[str, Any]):
        """
        Saves a task execution result to history.
        
        Args:
            session_id (str): Session identifier
            task (str): Task description
            urls (list): URLs processed during the task
            result (dict): Task execution result
        """
        try:
            urls_json = json.dumps(urls)
            result_json = json.dumps(result)
            
            self.cursor.execute('''
                INSERT INTO task_history (session_id, task, urls, result)
                VALUES (?, ?, ?, ?)
            ''', (session_id, task, urls_json, result_json))
            self.conn.commit()
            logger.info(f"Task result saved to history: {session_id}")
        except Exception as e:
            logger.error(f"Error saving task result: {str(e)}")

    def get_task_history(self, session_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves task execution history.
        
        Args:
            session_id (str, optional): Filter by session ID
            limit (int): Maximum number of history items to retrieve
            
        Returns:
            list: List of task history items
        """
        try:
            if session_id:
                self.cursor.execute('''
                    SELECT id, session_id, task, urls, result, timestamp
                    FROM task_history
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (session_id, limit))
            else:
                self.cursor.execute('''
                    SELECT id, session_id, task, urls, result, timestamp
                    FROM task_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
            rows = self.cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    "id": row[0],
                    "session_id": row[1],
                    "task": row[2],
                    "urls": json.loads(row[3]),
                    "result": json.loads(row[4]),
                    "timestamp": row[5]
                })
                
            return history
        except Exception as e:
            logger.error(f"Error retrieving task history: {str(e)}")
            return []

    def save_entity(self, session_id: str, entity_type: str, entity_value: str, 
                    source_url: str, context: str = ""):
        """
        Save an extracted entity for future reference.
        
        Args:
            session_id (str): Session identifier
            entity_type (str): Type of entity (e.g., 'person', 'company', 'location')
            entity_value (str): Value of the entity
            source_url (str): URL where the entity was found
            context (str, optional): Surrounding context of the entity
        """
        try:
            self.cursor.execute('''
                INSERT INTO entities (session_id, entity_type, entity_value, source_url, context)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, entity_type, entity_value, source_url, context))
            self.conn.commit()
            logger.debug(f"Entity saved: {entity_type}:{entity_value}")
        except Exception as e:
            logger.error(f"Error saving entity: {str(e)}")

    def get_entities(self, session_id: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve entities for a session.
        
        Args:
            session_id (str): Session identifier
            entity_type (str, optional): Filter by entity type
            
        Returns:
            list: List of entities
        """
        try:
            if entity_type:
                self.cursor.execute('''
                    SELECT entity_type, entity_value, source_url, context
                    FROM entities
                    WHERE session_id = ? AND entity_type = ?
                ''', (session_id, entity_type))
            else:
                self.cursor.execute('''
                    SELECT entity_type, entity_value, source_url, context
                    FROM entities
                    WHERE session_id = ?
                ''', (session_id,))
                
            rows = self.cursor.fetchall()
            
            entities = []
            for row in rows:
                entities.append({
                    "entity_type": row[0],
                    "entity_value": row[1],
                    "source_url": row[2],
                    "context": row[3]
                })
                
            return entities
        except Exception as e:
            logger.error(f"Error retrieving entities: {str(e)}")
            return []

    def close(self):
        """Close the database connection."""
        try:
            if self.conn:
                self.conn.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")