#!/usr/bin/env python3
"""
Production ChatBot Server
Comprehensive backend with database, authentication, rate limiting, and more
"""

import os
import json
import uuid
import sqlite3
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, session, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "chatbot.db")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    MAX_MESSAGE_LENGTH = 2000
    MAX_SESSIONS_PER_USER = 50
    SESSION_TIMEOUT_HOURS = 24
    RATE_LIMIT_CHAT = "10 per minute"
    MODEL = "llama-3.3-70b-versatile"

# Validate configuration
if not Config.GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables")
    raise RuntimeError("GROQ_API_KEY is required")

# Initialize Groq client
groq_client = Groq(api_key=Config.GROQ_API_KEY)

# System prompt
SYSTEM_PROMPT = {
    "role": "system", 
    "content": (
        "You are ChatBot, a helpful and conversational AI assistant powered by Groq. "
        "Be concise, friendly, and informative. Use markdown for formatting when appropriate. "
        "Always be respectful and helpful."
    )
}

# Database setup
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(Config.DATABASE_URL)
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
            is_active BOOLEAN DEFAULT 1
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
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tokens_used INTEGER DEFAULT 0,
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
            data JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # API usage table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            endpoint TEXT NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            response_time_ms INTEGER,
            status_code INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Database helper functions
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def log_analytics(event_type: str, user_id: Optional[int] = None, 
                 session_id: Optional[str] = None, data: Optional[Dict] = None):
    """Log analytics event"""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO analytics (event_type, user_id, session_id, data) VALUES (?, ?, ?, ?)",
            (event_type, user_id, session_id, json.dumps(data) if data else None)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log analytics: {e}")

def log_api_usage(user_id: Optional[int], endpoint: str, tokens_used: int = 0,
                 response_time_ms: int = 0, status_code: int = 200):
    """Log API usage"""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO api_usage (user_id, endpoint, tokens_used, response_time_ms, status_code) VALUES (?, ?, ?, ?, ?)",
            (user_id, endpoint, tokens_used, response_time_ms, status_code)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log API usage: {e}")

# Authentication helpers
def generate_api_key():
    """Generate a unique API key"""
    return f"cbk_{secrets.token_urlsafe(32)}"

def create_user(username: str, email: str, password: str) -> Dict:
    """Create a new user"""
    try:
        conn = get_db_connection()
        password_hash = generate_password_hash(password)
        api_key = generate_api_key()
        
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, api_key) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, api_key)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"User created: {username} (ID: {user_id})")
        return {"id": user_id, "username": username, "email": email, "api_key": api_key}
    except sqlite3.IntegrityError as e:
        logger.error(f"User creation failed: {e}")
        raise ValueError("Username or email already exists")

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user credentials"""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (username,)
    ).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        # Update last login
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user['id'],)
        )
        conn.commit()
        conn.close()
        
        return dict(user)
    return None

def authenticate_api_key(api_key: str) -> Optional[Dict]:
    """Authenticate API key"""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE api_key = ? AND is_active = 1",
        (api_key,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None

# Authentication decorators
def require_auth(f):
    """Require authentication for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        api_key = None
        
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
        elif 'api_key' in request.json if request.is_json else False:
            api_key = request.json['api_key']
        
        if not api_key:
            return jsonify({"error": "Authentication required"}), 401
        
        user = authenticate_api_key(api_key)
        if not user:
            return jsonify({"error": "Invalid API key"}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

# Chat session management
def create_chat_session(user_id: Optional[int] = None) -> str:
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO chat_sessions (id, user_id) VALUES (?, ?)",
        (session_id, user_id)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Created chat session: {session_id} for user: {user_id}")
    return session_id

def get_chat_session(session_id: str, user_id: Optional[int] = None) -> Optional[Dict]:
    """Get chat session details"""
    conn = get_db_connection()
    query = "SELECT * FROM chat_sessions WHERE id = ? AND is_active = 1"
    params = [session_id]
    
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    
    session = conn.execute(query, params).fetchone()
    conn.close()
    
    return dict(session) if session else None

def update_session_title(session_id: str, title: str):
    """Update session title"""
    conn = get_db_connection()
    conn.execute(
        "UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, session_id)
    )
    conn.commit()
    conn.close()

def get_session_messages(session_id: str, limit: int = 50) -> List[Dict]:
    """Get messages for a session"""
    conn = get_db_connection()
    messages = conn.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    
    return [dict(msg) for msg in reversed(messages)]

def save_message(session_id: str, role: str, content: str, tokens_used: int = 0):
    """Save a message to database"""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, tokens_used) VALUES (?, ?, ?, ?)",
        (session_id, role, content, tokens_used)
    )
    
    # Update session timestamp
    conn.execute(
        "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (session_id,)
    )
    
    conn.commit()
    conn.close()

# API Routes
@app.route("/")
def index():
    """Serve beautiful homepage"""
    log_analytics("page_view", data={"page": "home"})
    return render_template("home.html")

@app.route("/chat")
def chat_page():
    """Serve main chat interface"""
    log_analytics("page_view", data={"page": "chat"})
    return render_template("working.html")

@app.route("/auth")
def auth_page():
    """Serve authentication page"""
    return render_template("auth.html")

@app.route("/analytics")
def analytics_page():
    """Serve analytics dashboard"""
    return render_template("analytics.html")

@app.route("/api/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["username", "email", "password"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        user = create_user(data["username"], data["email"], data["password"])
        log_analytics("user_registered", user_id=user["id"])
        return jsonify({
            "message": "User created successfully",
            "api_key": user["api_key"]
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """User login"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["username", "password"]):
        return jsonify({"error": "Missing username or password"}), 400
    
    user = authenticate_user(data["username"], data["password"])
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    log_analytics("user_login", user_id=user["id"])
    return jsonify({
        "message": "Login successful",
        "api_key": user["api_key"],
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    })

@app.route("/chat", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT_CHAT)
def chat():
    """Chat endpoint with optional authentication"""
    start_time = datetime.now()
    
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message required"}), 400
    
    user_message = data["message"].strip()
    session_id = data.get("session_id")
    
    # Input validation
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    if len(user_message) > Config.MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"Message too long (max {Config.MAX_MESSAGE_LENGTH} characters)"}), 400
    
    # Authentication (optional)
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        api_key = auth_header[7:]
        user = authenticate_api_key(api_key)
        if user:
            user_id = user["id"]
    
    # Get or create session
    if not session_id:
        session_id = create_chat_session(user_id)
    else:
        session = get_chat_session(session_id, user_id)
        if not session:
            session_id = create_chat_session(user_id)
    
    # Get conversation history
    messages = get_session_messages(session_id, limit=20)
    
    # Prepare messages for Groq
    groq_messages = [SYSTEM_PROMPT]
    for msg in messages:
        groq_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    groq_messages.append({"role": "user", "content": user_message})
    
    try:
        # Call Groq API
        logger.info(f"Calling Groq API for session {session_id}")
        completion = groq_client.chat.completions.create(
            model=Config.MODEL,
            messages=groq_messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9,
        )
        
        reply = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens if hasattr(completion, 'usage') else 0
        
        # Save messages
        save_message(session_id, "user", user_message)
        save_message(session_id, "assistant", reply, tokens_used)
        
        # Update session title if first message
        if len(messages) == 0:
            title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            update_session_title(session_id, title)
        
        # Log analytics
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        log_analytics("chat_message", user_id=user_id, session_id=session_id, 
                     data={"tokens_used": tokens_used, "response_time_ms": response_time})
        log_api_usage(user_id, "/chat", tokens_used, response_time, 200)
        
        logger.info(f"Chat response generated: {len(reply)} chars, {tokens_used} tokens")
        
        return jsonify({
            "reply": reply,
            "session_id": session_id,
            "tokens_used": tokens_used
        })
        
    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        log_api_usage(user_id, "/chat", 0, 
                     int((datetime.now() - start_time).total_seconds() * 1000), 500)
        return jsonify({"error": "Failed to generate response"}), 500

@app.route("/api/sessions", methods=["GET"])
@require_auth
def get_user_sessions():
    """Get user's chat sessions"""
    user_id = g.current_user["id"]
    
    conn = get_db_connection()
    sessions = conn.execute("""
        SELECT cs.*, COUNT(m.id) as message_count 
        FROM chat_sessions cs 
        LEFT JOIN messages m ON cs.id = m.session_id 
        WHERE cs.user_id = ? AND cs.is_active = 1 
        GROUP BY cs.id 
        ORDER BY cs.updated_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    
    return jsonify({
        "sessions": [dict(session) for session in sessions]
    })

@app.route("/api/sessions/<session_id>", methods=["GET"])
@require_auth
def get_session_details(session_id):
    """Get session details and messages"""
    user_id = g.current_user["id"]
    
    session = get_chat_session(session_id, user_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    messages = get_session_messages(session_id)
    
    return jsonify({
        "session": session,
        "messages": messages
    })

@app.route("/api/sessions/<session_id>", methods=["DELETE"])
@require_auth
def delete_session(session_id):
    """Delete a chat session"""
    user_id = g.current_user["id"]
    
    session = get_chat_session(session_id, user_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    conn = get_db_connection()
    conn.execute(
        "UPDATE chat_sessions SET is_active = 0 WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    )
    conn.commit()
    conn.close()
    
    log_analytics("session_deleted", user_id=user_id, session_id=session_id)
    logger.info(f"Session {session_id} deleted by user {user_id}")
    
    return jsonify({"message": "Session deleted successfully"})

@app.route("/api/analytics", methods=["GET"])
@require_auth
def get_analytics():
    """Get user analytics"""
    user_id = g.current_user["id"]
    
    conn = get_db_connection()
    
    # Get usage stats
    stats = conn.execute("""
        SELECT 
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(*) as total_messages,
            SUM(tokens_used) as total_tokens,
            AVG(tokens_used) as avg_tokens_per_message
        FROM messages m
        JOIN chat_sessions cs ON m.session_id = cs.id
        WHERE cs.user_id = ?
    """, (user_id,)).fetchone()
    
    # Get recent activity
    recent_activity = conn.execute("""
        SELECT event_type, timestamp, data
        FROM analytics 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 50
    """, (user_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        "stats": dict(stats) if stats else {},
        "recent_activity": [dict(activity) for activity in recent_activity]
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "model": Config.MODEL
    })

@app.route("/api/status", methods=["GET"])
def server_status():
    """Get server status and statistics"""
    conn = get_db_connection()
    
    # Get basic stats
    user_count = conn.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()[0]
    session_count = conn.execute("SELECT COUNT(*) FROM chat_sessions WHERE is_active = 1").fetchone()[0]
    message_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    
    # Get recent activity
    recent_sessions = conn.execute("""
        SELECT COUNT(*) FROM chat_sessions 
        WHERE created_at > datetime('now', '-24 hours')
    """).fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "users": user_count,
        "total_sessions": session_count,
        "total_messages": message_count,
        "sessions_24h": recent_sessions,
        "uptime": datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded", "message": str(e.description)}), 429

# Initialize and run
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting ChatBot Production Server")
    logger.info(f"Model: {Config.MODEL}")
    logger.info(f"Database: {Config.DATABASE_URL}")
    logger.info("=" * 60)
    
    # Initialize database
    init_database()
    
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Run server
    app.run(
        debug=False,
        host="0.0.0.0",
        port=port,
        threaded=True
    )
else:
    # For serverless deployments (Vercel, etc.)
    # Initialize database when module is imported
    init_database()