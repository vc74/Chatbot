import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

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
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "id": session_id,
            "title": "New chat",
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id")

    if not user_message:
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

    # Prepare messages for Groq
    messages = [SYSTEM_PROMPT] + [
        {"role": m["role"], "content": m["content"]} 
        for m in chat_session["messages"][-20:]  # Last 20 messages
    ]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9,
        )
        reply = completion.choices[0].message.content
        
        # Add assistant reply to session
        chat_session["messages"].append({
            "role": "assistant", 
            "content": reply,
            "timestamp": datetime.now().isoformat()
        })
        
        chat_session["updated_at"] = datetime.now().isoformat()
        
        return jsonify({
            "reply": reply, 
            "session_id": session_id,
            "title": chat_session["title"]
        })

    except Exception as e:
        app.logger.error("Groq API error: %s", str(e))
        return jsonify({"reply": f"⚠️ Groq API error: {str(e)}"}), 500


@app.route("/chat/history")
def chat_history():
    """Get list of all chat sessions"""
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
    return jsonify({"sessions": sessions})


@app.route("/chat/session/<session_id>")
def get_chat_session_route(session_id):
    """Get a specific chat session"""
    if session_id in chat_sessions:
        return jsonify(chat_sessions[session_id])
    return jsonify({"error": "Session not found"}), 404


@app.route("/chat/session/<session_id>", methods=["DELETE"])
def delete_chat_session(session_id):
    """Delete a chat session"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return jsonify({"message": "Session deleted"})
    return jsonify({"error": "Session not found"}), 404


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
