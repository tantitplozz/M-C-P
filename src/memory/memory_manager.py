"""
GOD-TIER AUTOBUY STACK - Memory Manager
Production-ready memory management system
"""

import asyncio
import json
import logging
import redis
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

class MemoryManager:
    """
    Production-ready Memory Manager
    Handles session memory, persistent storage, and caching
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Redis configuration
        redis_config = config.get('database', {}).get('memory', {})
        self.redis_host = redis_config.get('host', 'localhost')
        self.redis_port = redis_config.get('port', 6379)
        self.redis_db = redis_config.get('db', 0)
        self.redis_password = redis_config.get('password')

        # SQLite configuration
        storage_config = config.get('database', {}).get('storage', {})
        self.db_path = storage_config.get('path', 'data/autobuy.db')

        # Memory settings
        memory_config = config.get('memory', {})
        self.max_sessions = memory_config.get('max_sessions', 1000)
        self.session_ttl = memory_config.get('session_ttl', 3600)
        self.max_memory_per_session = memory_config.get('max_memory_per_session', 1000000)

        # Initialize connections
        self.redis_client = None
        self.db_path_obj = Path(self.db_path)

        self.logger.info("Memory Manager initialized")

    async def initialize(self):
        """Initialize memory manager"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True
            )

            # Test Redis connection
            await self.redis_client.ping()
            self.logger.info("Redis connection established")

            # Initialize SQLite database
            self.db_path_obj.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()

            self.logger.info("Memory Manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Memory Manager initialization failed: {e}")
            raise

    async def store_task_result(self, task_id: str, result: Any) -> bool:
        """Store task result in persistent storage"""
        try:
            # Store in Redis for quick access
            if self.redis_client:
                await self.redis_client.setex(
                    f"task:{task_id}",
                    self.session_ttl,
                    json.dumps(result, default=str)
                )

            # Store in SQLite for persistence
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'INSERT INTO task_results (task_id, result_data) VALUES (?, ?)',
                (task_id, json.dumps(result, default=str))
            )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Task result storage failed: {e}")
            return False

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result from memory or storage"""
        try:
            # Try Redis first
            if self.redis_client:
                result = await self.redis_client.get(f"task:{task_id}")
                if result:
                    return json.loads(result)

            # Fallback to SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT result_data FROM task_results WHERE task_id = ? ORDER BY created_at DESC LIMIT 1',
                (task_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return json.loads(row[0])

            return None

        except Exception as e:
            self.logger.error(f"Task result retrieval failed: {e}")
            return None

    async def store_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Store session data"""
        try:
            # Check memory usage
            data_size = len(json.dumps(data, default=str))
            if data_size > self.max_memory_per_session:
                self.logger.warning(f"Session data too large: {data_size} bytes")
                return False

            # Store in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"session:{session_id}",
                    self.session_ttl,
                    json.dumps(data, default=str)
                )

            # Store in SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if session exists
            cursor.execute(
                'SELECT id FROM session_data WHERE session_id = ?',
                (session_id,)
            )

            if cursor.fetchone():
                # Update existing session
                cursor.execute(
                    'UPDATE session_data SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?',
                    (json.dumps(data, default=str), session_id)
                )
            else:
                # Insert new session
                cursor.execute(
                    'INSERT INTO session_data (session_id, data) VALUES (?, ?)',
                    (session_id, json.dumps(data, default=str))
                )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Session data storage failed: {e}")
            return False

    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            # Try Redis first
            if self.redis_client:
                result = await self.redis_client.get(f"session:{session_id}")
                if result:
                    return json.loads(result)

            # Fallback to SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT data FROM session_data WHERE session_id = ? ORDER BY updated_at DESC LIMIT 1',
                (session_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return json.loads(row[0])

            return None

        except Exception as e:
            self.logger.error(f"Session data retrieval failed: {e}")
            return None

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            # Calculate expiry time
            expiry_time = datetime.now() - timedelta(seconds=self.session_ttl)

            # Clean up SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'DELETE FROM session_data WHERE updated_at < ?',
                (expiry_time,)
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} expired sessions")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Session cleanup failed: {e}")
            return 0

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            stats = {
                "timestamp": datetime.now().isoformat(),
                "redis_connected": False,
                "sqlite_size": 0,
                "active_sessions": 0,
                "total_tasks": 0
            }

            # Redis stats
            if self.redis_client:
                try:
                    redis_info = await self.redis_client.info()
                    stats["redis_connected"] = True
                    stats["redis_memory"] = redis_info.get('used_memory', 0)
                    stats["redis_keys"] = await self.redis_client.dbsize()
                except Exception as e:
                    self.logger.warning(f"Redis stats failed: {e}")

            # SQLite stats
            if self.db_path_obj.exists():
                stats["sqlite_size"] = self.db_path_obj.stat().st_size

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM session_data')
                stats["active_sessions"] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM task_results')
                stats["total_tasks"] = cursor.fetchone()[0]

                conn.close()

            return stats

        except Exception as e:
            self.logger.error(f"Memory stats failed: {e}")
            return {"error": str(e)}

    async def clear_all_data(self) -> bool:
        """Clear all data (use with caution)"""
        try:
            # Clear Redis
            if self.redis_client:
                await self.redis_client.flushdb()

            # Clear SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM session_data')
            cursor.execute('DELETE FROM task_results')

            conn.commit()
            conn.close()

            self.logger.info("All memory data cleared")
            return True

        except Exception as e:
            self.logger.error(f"Data clearing failed: {e}")
            return False
