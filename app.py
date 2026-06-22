import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_message = (data.get("message") or "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"reply": "Your message was empty — say something!"}), 200

    # Sanitize history: only keep valid role/content pairs
    clean_history = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
    ]

    messages = [SYSTEM_PROMPT] + clean_history + [{"role": "user", "content": user_message}]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9,
        )
        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        app.logger.error("Groq API error: %s", str(e))
        return jsonify({"reply": f"⚠️ Groq API error: {str(e)}"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
