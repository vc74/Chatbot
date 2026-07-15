"""
Database management for ChatBot Server
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        else:
            conn.commit()
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    subscription_tier TEXT DEFAULT 'free',
                    usage_limit INTEGER DEFAULT 100,
                    usage_count INTEGER DEFAULT 0,
                    reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Chat sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    title TEXT NOT NULL DEFAULT 'New Chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    model_used TEXT DEFAULT 'llama-3.3-70b-versatile',
                    total_tokens INTEGER DEFAULT 0,
                    message_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tokens_used INTEGER DEFAULT 0,
                    response_time_ms INTEGER DEFAULT 0,
                    model_used TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                )
            ''')
            
            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    session_id TEXT,
                    endpoint TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    data JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # API usage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    response_time_ms INTEGER DEFAULT 0,
                    status_code INTEGER DEFAULT 200,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id TEXT,
                    message_id INTEGER,
                    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                    feedback_text TEXT,
                    feedback_type TEXT DEFAULT 'general',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            ''')
            
            # System logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    logger_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    exception_traceback TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON chat_sessions (updated_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics (event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_api_key ON users (api_key)')
            
        logger.info("Database initialized successfully")
    
    # User management
    def create_user(self, username: str, email: str, password_hash: str, api_key: str) -> int:
        """Create a new user"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash, api_key) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, api_key)
            )
            return cursor.lastrowid
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1", 
                (username,)
            ).fetchone()
            return dict(user) if user else None
    
    def get_user_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Get user by API key"""
        with self.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE api_key = ? AND is_active = 1", 
                (api_key,)
            ).fetchone()
            return dict(user) if user else None
    
    def update_user_login(self, user_id: int):
        """Update user's last login timestamp"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
    
    def increment_user_usage(self, user_id: int, tokens: int = 1):
        """Increment user's usage count"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET usage_count = usage_count + ? WHERE id = ?",
                (tokens, user_id)
            )
    
    # Session management
    def create_session(self, session_id: str, user_id: Optional[int] = None) -> str:
        """Create a new chat session"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO chat_sessions (id, user_id) VALUES (?, ?)",
                (session_id, user_id)
            )
            return session_id
    
    def get_session(self, session_id: str, user_id: Optional[int] = None) -> Optional[Dict]:
        """Get session by ID"""
        with self.get_connection() as conn:
            query = "SELECT * FROM chat_sessions WHERE id = ? AND is_active = 1"
            params = [session_id]
            
            if user_id is not None:
                query += " AND user_id = ?"
                params.append(user_id)
            
            session = conn.execute(query, params).fetchone()
            return dict(session) if session else None
    
    def update_session(self, session_id: str, **kwargs):
        """Update session fields"""
        if not kwargs:
            return
        
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(session_id)
        
        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE chat_sessions SET {', '.join(fields)} WHERE id = ?",
                values
            )
    
    def get_user_sessions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's chat sessions"""
        with self.get_connection() as conn:
            sessions = conn.execute("""
                SELECT cs.*, COUNT(m.id) as message_count 
                FROM chat_sessions cs 
                LEFT JOIN messages m ON cs.id = m.session_id 
                WHERE cs.user_id = ? AND cs.is_active = 1 
                GROUP BY cs.id 
                ORDER BY cs.updated_at DESC 
                LIMIT ?
            """, (user_id, limit)).fetchall()
            return [dict(session) for session in sessions]
    
    def delete_session(self, session_id: str, user_id: int):
        """Soft delete a session"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE chat_sessions SET is_active = 0 WHERE id = ? AND user_id = ?",
                (session_id, user_id)
            )
    
    # Message management
    def save_message(self, session_id: str, role: str, content: str, 
                    tokens_used: int = 0, response_time_ms: int = 0, model_used: str = None) -> int:
        """Save a message"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO messages (session_id, role, content, tokens_used, response_time_ms, model_used) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, role, content, tokens_used, response_time_ms, model_used)
            )
            
            # Update session stats
            conn.execute(
                "UPDATE chat_sessions SET total_tokens = total_tokens + ?, message_count = message_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (tokens_used, session_id)
            )
            
            return cursor.lastrowid
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get messages for a session"""
        with self.get_connection() as conn:
            messages = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            ).fetchall()
            return [dict(msg) for msg in messages]
    
    # Analytics and logging
    def log_analytics(self, event_type: str, user_id: Optional[int] = None, 
                     session_id: Optional[str] = None, endpoint: Optional[str] = None,
                     ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                     data: Optional[Dict] = None):
        """Log analytics event"""
        import json
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO analytics (event_type, user_id, session_id, endpoint, ip_address, user_agent, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event_type, user_id, session_id, endpoint, ip_address, user_agent, 
                 json.dumps(data) if data else None)
            )
    
    def log_api_usage(self, user_id: Optional[int], endpoint: str, method: str,
                     tokens_used: int = 0, response_time_ms: int = 0, 
                     status_code: int = 200, ip_address: Optional[str] = None):
        """Log API usage"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO api_usage (user_id, endpoint, method, tokens_used, response_time_ms, status_code, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, endpoint, method, tokens_used, response_time_ms, status_code, ip_address)
            )
    
    def save_feedback(self, user_id: Optional[int], session_id: Optional[str],
                     message_id: Optional[int], rating: int, feedback_text: str = None,
                     feedback_type: str = 'general'):
        """Save user feedback"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO feedback (user_id, session_id, message_id, rating, feedback_text, feedback_type) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, session_id, message_id, rating, feedback_text, feedback_type)
            )
    
    # Statistics and reporting
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        with self.get_connection() as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(DISTINCT cs.id) as total_sessions,
                    COUNT(m.id) as total_messages,
                    COALESCE(SUM(m.tokens_used), 0) as total_tokens,
                    COALESCE(AVG(m.tokens_used), 0) as avg_tokens_per_message,
                    COALESCE(AVG(m.response_time_ms), 0) as avg_response_time
                FROM chat_sessions cs
                LEFT JOIN messages m ON cs.id = m.session_id
                WHERE cs.user_id = ? AND cs.is_active = 1
            """, (user_id,)).fetchone()
            
            recent_activity = conn.execute(
                "SELECT COUNT(*) as sessions_today FROM chat_sessions WHERE user_id = ? AND DATE(created_at) = DATE('now')",
                (user_id,)
            ).fetchone()
            
            result = dict(stats) if stats else {}
            result.update(dict(recent_activity) if recent_activity else {})
            return result
    
    def get_system_stats(self) -> Dict:
        """Get system-wide statistics"""
        with self.get_connection() as conn:
            stats = {}
            
            # User stats
            user_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN last_login > datetime('now', '-7 days') THEN 1 END) as active_users_7d,
                    COUNT(CASE WHEN last_login > datetime('now', '-30 days') THEN 1 END) as active_users_30d
                FROM users WHERE is_active = 1
            """).fetchone()
            stats.update(dict(user_stats))
            
            # Session stats
            session_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN created_at > datetime('now', '-24 hours') THEN 1 END) as sessions_24h,
                    COUNT(CASE WHEN created_at > datetime('now', '-7 days') THEN 1 END) as sessions_7d
                FROM chat_sessions WHERE is_active = 1
            """).fetchone()
            stats.update(dict(session_stats))
            
            # Message stats
            message_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COALESCE(SUM(tokens_used), 0) as total_tokens,
                    COALESCE(AVG(response_time_ms), 0) as avg_response_time
                FROM messages
            """).fetchone()
            stats.update(dict(message_stats))
            
            return stats
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old data"""
        with self.get_connection() as conn:
            # Delete old inactive sessions
            conn.execute(
                "DELETE FROM chat_sessions WHERE is_active = 0 AND updated_at < datetime('now', '-? days')",
                (days,)
            )
            
            # Delete old analytics data
            conn.execute(
                "DELETE FROM analytics WHERE timestamp < datetime('now', '-? days')",
                (days,)
            )
            
            # Delete old API usage data
            conn.execute(
                "DELETE FROM api_usage WHERE timestamp < datetime('now', '-? days')",
                (days,)
            )
            
            logger.info(f"Cleaned up data older than {days} days")