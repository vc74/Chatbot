"""
Vercel-compatible ChatBot Server
Serverless deployment version
"""

import os
import json
import uuid
import logging
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, session, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
            
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "vercel-deployment-secret-key")

# Configure logging (console only for Vercel)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    MAX_MESSAGE_LENGTH = 2000
    MODEL = "llama-3.3-70b-versatile"

# In-memory storage (for serverless - resets on each deployment)
chat_sessions = {}
users = {}
analytics_log = []

# Initialize Groq client only if API key exists
groq_client = None
if Config.GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=Config.GROQ_API_KEY)
        logger.info("Groq client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")

# System prompt
SYSTEM_PROMPT = {
    "role": "system", 
    "content": (
        "You are ChatBot, a helpful and conversational AI assistant powered by Groq. "
        "Be concise, friendly, and informative. Use markdown for formatting when appropriate. "
        "Always be respectful and helpful."
    )
}

# Helper functions
def generate_api_key():
    """Generate a unique API key"""
    import secrets
    return f"cbk_{secrets.token_urlsafe(32)}"

def log_analytics(event_type: str, user_id: Optional[int] = None, 
                 session_id: Optional[str] = None, data: Optional[Dict] = None):
    """Log analytics event to memory"""
    try:
        analytics_log.append({
            "event_type": event_type,
            "user_id": user_id,
            "session_id": session_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 1000 events
        if len(analytics_log) > 1000:
            analytics_log.pop(0)
    except Exception as e:
        logger.error(f"Failed to log analytics: {e}")

def create_user(username: str, email: str, password: str) -> Dict:
    """Create a new user (in-memory)"""
    if username in users:
        raise ValueError("Username already exists")
    
    user_id = len(users) + 1
    api_key = generate_api_key()
    
    users[username] = {
        "id": user_id,
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password),
        "api_key": api_key,
        "created_at": datetime.now().isoformat()
    }
    
    logger.info(f"User created: {username}")
    return {"id": user_id, "username": username, "email": email, "api_key": api_key}

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user credentials"""
    user = users.get(username)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def authenticate_api_key(api_key: str) -> Optional[Dict]:
    """Authenticate API key"""
    for user in users.values():
        if user.get('api_key') == api_key:
            return user
    return None

def require_auth(f):
    """Require authentication for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        api_key = None
        
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
        elif request.is_json and 'api_key' in request.json:
            api_key = request.json['api_key']
        
        if not api_key:
            return jsonify({"error": "Authentication required"}), 401
        
        user = authenticate_api_key(api_key)
        if not user:
            return jsonify({"error": "Invalid API key"}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def create_chat_session(user_id: Optional[int] = None) -> str:
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    chat_sessions[session_id] = {
        "id": session_id,
        "user_id": user_id,
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    logger.info(f"Created chat session: {session_id}")
    return session_id

def get_chat_session(session_id: str) -> Optional[Dict]:
    """Get chat session details"""
    return chat_sessions.get(session_id)

def save_message(session_id: str, role: str, content: str, tokens_used: int = 0):
    """Save a message to session"""
    if session_id in chat_sessions:
        chat_sessions[session_id]["messages"].append({
            "role": role,
            "content": content,
            "tokens_used": tokens_used,
            "timestamp": datetime.now().isoformat()
        })
        chat_sessions[session_id]["updated_at"] = datetime.now().isoformat()

def get_session_messages(session_id: str, limit: int = 20) -> List[Dict]:
    """Get messages for a session"""
    if session_id in chat_sessions:
        messages = chat_sessions[session_id]["messages"]
        return messages[-limit:] if len(messages) > limit else messages
    return []

# Routes
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
def chat():
    """Chat endpoint"""
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
    
    # Check if Groq client is initialized
    if not groq_client:
        return jsonify({"error": "AI service not available. Please check configuration."}), 503
    
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
        if not get_chat_session(session_id):
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
        if len(messages) == 0 and session_id in chat_sessions:
            title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            chat_sessions[session_id]["title"] = title
        
        # Log analytics
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        log_analytics("chat_message", user_id=user_id, session_id=session_id, 
                     data={"tokens_used": tokens_used, "response_time_ms": response_time})
        
        logger.info(f"Chat response generated: {len(reply)} chars, {tokens_used} tokens")
        
        return jsonify({
            "reply": reply,
            "session_id": session_id,
            "tokens_used": tokens_used
        })
        
    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate response. Please try again."}), 500

@app.route("/api/sessions", methods=["GET"])
@require_auth
def get_user_sessions():
    """Get user's chat sessions"""
    user_id = g.current_user["id"]
    
    user_sessions = [
        {
            "id": sid,
            "title": s["title"],
            "created_at": s["created_at"],
            "updated_at": s["updated_at"],
            "message_count": len(s["messages"])
        }
        for sid, s in chat_sessions.items()
        if s.get("user_id") == user_id and s.get("is_active")
    ]
    
    # Sort by updated_at descending
    user_sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    
    return jsonify({"sessions": user_sessions})

@app.route("/api/sessions/<session_id>", methods=["GET"])
@require_auth
def get_session_details(session_id):
    """Get session details and messages"""
    user_id = g.current_user["id"]
    
    session = get_chat_session(session_id)
    if not session or session.get("user_id") != user_id:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({
        "session": {
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"]
        },
        "messages": session["messages"]
    })

@app.route("/api/sessions/<session_id>", methods=["DELETE"])
@require_auth
def delete_session(session_id):
    """Delete a chat session"""
    user_id = g.current_user["id"]
    
    session = get_chat_session(session_id)
    if not session or session.get("user_id") != user_id:
        return jsonify({"error": "Session not found"}), 404
    
    chat_sessions[session_id]["is_active"] = False
    log_analytics("session_deleted", user_id=user_id, session_id=session_id)
    
    return jsonify({"message": "Session deleted successfully"})

@app.route("/api/analytics", methods=["GET"])
@require_auth
def get_analytics():
    """Get user analytics"""
    user_id = g.current_user["id"]
    
    # Calculate stats from in-memory data
    user_sessions = [s for s in chat_sessions.values() if s.get("user_id") == user_id]
    total_messages = sum(len(s["messages"]) for s in user_sessions)
    total_tokens = sum(
        msg.get("tokens_used", 0) 
        for s in user_sessions 
        for msg in s["messages"]
    )
    
    stats = {
        "total_sessions": len(user_sessions),
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "avg_tokens_per_message": total_tokens / total_messages if total_messages > 0 else 0
    }
    
    # Get recent activity for this user
    recent_activity = [
        a for a in analytics_log 
        if a.get("user_id") == user_id
    ][-50:]
    
    return jsonify({
        "stats": stats,
        "recent_activity": recent_activity
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-vercel",
        "model": Config.MODEL,
        "groq_available": groq_client is not None
    })

@app.route("/api/status", methods=["GET"])
def server_status():
    """Get server status and statistics"""
    return jsonify({
        "users": len(users),
        "total_sessions": len(chat_sessions),
        "total_messages": sum(len(s["messages"]) for s in chat_sessions.values()),
        "sessions_24h": len(chat_sessions),
        "uptime": datetime.now().isoformat(),
        "environment": "vercel-serverless"
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Vercel serverless handler
def handler(request):
    """Vercel serverless handler"""
    with app.request_context(request.environ):
        return app.full_dispatch_request()

# For local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
