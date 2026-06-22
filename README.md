# ChatBot 🤖

A modern AI chatbot powered by **Groq** (LLaMA 3) with a sleek dark-themed web UI.

## Features

- ⚡ **Blazing fast** responses via Groq's inference API
- 🧠 **Multi-turn memory** — full conversation context sent with each request
- 📝 **Markdown rendering** — bot replies support code blocks, bold, lists, etc.
- 🎨 **Polished dark UI** — typing animation, suggestion chips, auto-resize input
- 🗑️ **Clear chat** button to start fresh
- 📱 **Responsive** — works on mobile and desktop
- 🔒 **API key secured** via `.env` (never committed to git)

## Tech Stack

| Layer    | Tech                        |
|----------|-----------------------------|
| Backend  | Python · Flask              |
| LLM      | Groq API · LLaMA 3.3 70B Versatile |
| Frontend | HTML · CSS · Vanilla JS     |
| Markdown | marked.js + highlight.js    |

## Getting Started

### Prerequisites

- Python 3.8+
- A [Groq API key](https://console.groq.com)

### Installation

```bash
git clone https://github.com/vc74/Chatbot.git
cd Chatbot
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

### Run

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure

```
Chatbot/
├── app.py              # Flask backend + Groq integration
├── templates/
│   └── index.html      # Full chat UI (HTML/CSS/JS)
├── .env                # Your Groq API key (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | Route     | Description                        |
|--------|-----------|------------------------------------|
| GET    | `/`       | Serve the chat UI                  |
| POST   | `/chat`   | Send a message, receive AI reply   |
| GET    | `/health` | Health check + model info          |

### POST `/chat` payload

```json
{
  "message": "Hello!",
  "history": [
    { "role": "user",      "content": "Hi" },
    { "role": "assistant", "content": "Hey there!" }
  ]
}
```
