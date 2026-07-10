# ChatBot 🤖

A modern AI chatbot powered by **Groq** (LLaMA 3.3 70B) with advanced voice assistance and a sleek Gemini-inspired UI.

## ✨ Features

### 🎤 **Advanced Voice Assistant**
- **Voice input** with real-time transcription and confidence levels
- **Text-to-speech** responses with adjustable speed and voice selection
- **Voice commands** for hands-free control
- **Wake word activation** ("Hey ChatBot")
- **Continuous listening** mode
- **Speech controls** with visual feedback

### 💬 **Smart Chat Features**
- ⚡ **Blazing fast** responses via Groq's LLaMA 3.3 70B
- 🧠 **Multi-turn conversation** with full context memory
- 💾 **Persistent chat history** — sessions saved and restored
- 📝 **Markdown rendering** — code blocks, lists, formatting
- 🗑️ **Session management** — create, load, delete chats
- 🎨 **Gemini-inspired UI** — modern dark theme with smooth animations

### 🎙️ **Voice Commands**
- "Clear chat" — Start new conversation
- "Stop speaking" — Cancel current speech
- "Repeat that" — Replay last response
- "Send message" — Submit typed message
- "Hey ChatBot [question]" — Wake word activation

### ⌨️ **Keyboard Shortcuts**
- **Enter** — Send message
- **Shift + Enter** — New line
- **Ctrl/Cmd + M** — Toggle voice input
- **Escape** — Close panels / stop listening

## 🎨 UI Features

- 📱 **Fully responsive** — works on mobile and desktop
- 🌙 **Dark theme** with carefully chosen color palette
- ✨ **Smooth animations** and micro-interactions
- 🎭 **Voice visualizer** with animated waveforms
- 💬 **Speech bubble** showing what's being spoken
- ⚙️ **Settings panel** for voice customization

## Tech Stack

| Layer      | Tech                                    |
|------------|-----------------------------------------|
| Backend    | Python · Flask                          |
| LLM        | Groq API · LLaMA 3.3 70B Versatile      |
| Frontend   | HTML · CSS · Vanilla JavaScript         |
| Voice      | Web Speech API (Recognition & Synthesis)|
| Markdown   | marked.js + highlight.js                |
| Storage    | In-memory sessions (upgradeable to DB)  |

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

| Method | Route                    | Description                        |
|--------|--------------------------|------------------------------------|
| GET    | `/`                      | Serve the chat UI                  |
| POST   | `/chat`                  | Send message, receive AI reply     |
| GET    | `/chat/history`          | Get list of all chat sessions      |
| GET    | `/chat/session/<id>`     | Get specific chat session          |
| DELETE | `/chat/session/<id>`     | Delete a chat session              |
| GET    | `/health`                | Health check + model info          |

### POST `/chat` payload

```json
{
  "message": "Hello!",
  "session_id": "optional-session-id"
}
```

### Response

```json
{
  "reply": "AI response text",
  "session_id": "session-uuid",
  "title": "Chat title"
}
```

## 🎤 Voice Features Setup

### Browser Compatibility
- **Chrome/Edge:** Full support (recommended)
- **Safari:** Partial support (no continuous listening)
- **Firefox:** Limited support

### Permissions
The chatbot will request microphone access on first use. Grant permission to enable voice features.

### Voice Settings
1. Click the **microphone gear icon** in the header
2. Adjust settings:
   - **Voice Commands:** Enable/disable command recognition
   - **Auto Speech:** Toggle automatic TTS responses
   - **Wake Word:** Enable continuous "Hey ChatBot" detection
   - **Speech Speed:** Adjust playback rate (0.5x - 2.0x)
   - **Voice Type:** Select preferred system voice

## 🚀 Usage Examples

### Voice Input
```
1. Click microphone button in header
2. Say your message
3. Message appears in input box
4. Press Enter or say "send message"
```

### Voice Commands
```
"Hey ChatBot, tell me a joke"
"Clear chat"
"Stop speaking"
"Repeat that"
```

### Chat History
```
1. Previous chats appear in left sidebar
2. Click any chat to restore conversation
3. Click "New chat" to start fresh
```
