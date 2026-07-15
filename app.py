import os
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate API key on startup
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are ChatBot, a friendly, helpful, and concise AI assistant powered by Groq. "
        "Keep responses clear and conversational. Use markdown formatting where appropriate "
        "(code blocks, bullet points, bold text). Avoid unnecessary verbosity."
    ),
}

MODEL = "llama-3.3-70b-versatile"

# Chat history storage (in production, use a database)
chat_sessions = {}

def get_chat_session(session_id=None):
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"Created new chat session: {session_id}")
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "id": session_id,
            "title": "New chat",
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        logger.info(f"Initialized session data for: {session_id}")
    
    return chat_sessions[session_id]

def update_chat_title(session_id, first_message):
    """Generate a title from the first user message"""
    if session_id in chat_sessions:
        # Take first 50 characters of the message as title
        title = first_message[:50].strip()
        if len(first_message) > 50:
            title += "..."
        chat_sessions[session_id]["title"] = title
        chat_sessions[session_id]["updated_at"] = datetime.now().isoformat()
        logger.info(f"Updated title for session {session_id}: {title}")


@app.route("/")
def index():
    logger.info("Main page accessed")
    return render_template("working.html")


@app.route("/old")
def old():
    logger.info("Old page accessed")
    return render_template("index.html")


@app.route("/simple")
def simple():
    logger.info("Simple page accessed")
    return app.send_static_file("simple.html")


@app.route("/chat", methods=["POST"])
def chat():
    logger.info("Chat request received")
    data = request.get_json(silent=True)
    if not data:
        logger.error("Invalid JSON in request")
        return jsonify({"error": "Invalid JSON"}), 400

    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id")
    
    logger.info(f"Message from session {session_id}: {user_message[:50]}...")

    if not user_message:
        logger.warning("Empty message received")
        return jsonify({"reply": "Your message was empty — say something!"}), 200

    # Get or create chat session
    chat_session = get_chat_session(session_id)
    session_id = chat_session["id"]

    # Update title if this is the first message
    if not chat_session["messages"]:
        update_chat_title(session_id, user_message)

    # Add user message to session
    chat_session["messages"].append({
        "role": "user", 
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })
    logger.info(f"Added user message to session {session_id}")

    # Prepare messages for Groq
    messages = [SYSTEM_PROMPT] + [
        {"role": m["role"], "content": m["content"]} 
        for m in chat_session["messages"][-20:]  # Last 20 messages
    ]

    try:
        logger.info(f"Calling Groq API for session {session_id}")
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9,
        )
        reply = completion.choices[0].message.content
        logger.info(f"Received response from Groq: {len(reply)} characters")
        
        # Add assistant reply to session
        chat_session["messages"].append({
            "role": "assistant", 
            "content": reply,
            "timestamp": datetime.now().isoformat()
        })
        
        chat_session["updated_at"] = datetime.now().isoformat()
        logger.info(f"Session {session_id} updated successfully")
        
        return jsonify({
            "reply": reply, 
            "session_id": session_id,
            "title": chat_session["title"]
        })

    except Exception as e:
        logger.error(f"Groq API error for session {session_id}: {str(e)}", exc_info=True)
        return jsonify({"reply": f"⚠️ Groq API error: {str(e)}"}), 500


@app.route("/chat/history")
def chat_history():
    """Get list of all chat sessions"""
    logger.info("Chat history requested")
    sessions = []
    for session_id, session_data in chat_sessions.items():
        sessions.append({
            "id": session_id,
            "title": session_data["title"],
            "updated_at": session_data["updated_at"],
            "message_count": len(session_data["messages"])
        })
    
    # Sort by updated_at descending
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    logger.info(f"Returning {len(sessions)} chat sessions")
    return jsonify({"sessions": sessions})


@app.route("/chat/session/<session_id>")
def get_chat_session_route(session_id):
    """Get a specific chat session"""
    logger.info(f"Session {session_id} requested")
    if session_id in chat_sessions:
        return jsonify(chat_sessions[session_id])
    logger.warning(f"Session {session_id} not found")
    return jsonify({"error": "Session not found"}), 404


@app.route("/chat/session/<session_id>", methods=["DELETE"])
def delete_chat_session(session_id):
    """Delete a chat session"""
    logger.info(f"Deleting session {session_id}")
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        logger.info(f"Session {session_id} deleted successfully")
        return jsonify({"message": "Session deleted"})
    logger.warning(f"Attempted to delete non-existent session {session_id}")
    return jsonify({"error": "Session not found"}), 404


@app.route("/health")
def health():
    logger.info("Health check requested")
    return jsonify({"status": "ok", "model": MODEL})


@app.route("/logs")
def view_logs():
    """View recent logs"""
    try:
        with open('chatbot.log', 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-100:]  # Last 100 lines
        return jsonify({"logs": recent_logs})
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/logs/view")
def logs_page():
    """Render logs viewer page"""
    return render_template("logs.html")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Starting ChatBot Application")
    logger.info(f"Model: {MODEL}")
    logger.info(f"Debug mode: {app.debug}")
    logger.info("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
