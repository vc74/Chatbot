# 🤖 ChatBot - Complete Production Backend

A sophisticated chatbot powered by **Groq's LLaMA 3.3 70B** with comprehensive backend infrastructure, user authentication, analytics, and production-ready features.

## 🌟 Features

### Core Features
- **Advanced AI Chat**: Powered by Groq's LLaMA 3.3 70B Versatile model
- **Real-time Responses**: Fast, intelligent conversations with markdown support
- **Session Management**: Persistent chat sessions with history
- **Syntax Highlighting**: Code blocks with proper formatting

### Production Backend
- **User Authentication**: Secure registration and login system
- **API Key Management**: Generate and manage API keys for users
- **Rate Limiting**: Configurable limits to prevent abuse
- **Database Integration**: SQLite with comprehensive data models
- **Analytics Dashboard**: User activity, usage stats, and insights
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

### Security & Performance
- **CORS Support**: Cross-origin resource sharing configuration
- **Input Validation**: Secure handling of user inputs
- **Error Handling**: Graceful error responses and logging
- **Production Ready**: Gunicorn support for deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Groq API key (get one at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone or download the project**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file with your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   SECRET_KEY=your-secret-key-for-sessions
   DATABASE_URL=chatbot_production.db
   DEBUG=False
   ```

4. **Start the server:**
   
   **Easy way (Windows):**
   ```bash
   start_chatbot.bat
   ```
   
   **Manual way:**
   ```bash
   python run_server.py
   # or
   python server.py
   ```

5. **Access the application:**
   - Main chat interface: [http://localhost:5000](http://localhost:5000)
   - Authentication page: [http://localhost:5000/auth](http://localhost:5000/auth)
   - Analytics dashboard: [http://localhost:5000/analytics](http://localhost:5000/analytics)

## 📁 Project Structure

```
Chatbot/
├── server.py              # Production server with full backend
├── app.py                 # Simple development server
├── database.py            # Database management utilities
├── config.py              # Configuration settings
├── run_server.py          # Server runner script
├── start_chatbot.bat      # Windows startup script
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── templates/
│   ├── working.html       # Main chat interface
│   ├── auth.html          # Authentication page
│   ├── analytics.html     # Analytics dashboard
│   ├── logs.html          # Log viewer
│   └── index.html         # Alternative interface
├── static/
│   └── simple.html        # Simple chat interface
└── README.md              # This file
```

## 🎯 Usage Guide

### For Users

1. **Visit the ChatBot**: Go to [http://localhost:5000](http://localhost:5000)
2. **Optional Login**: Click "Login" to create an account for advanced features
3. **Start Chatting**: Type your message and press Enter
4. **View Analytics**: If logged in, click the 📊 button to see usage statistics

### For Developers

#### API Endpoints

**Authentication:**
- `POST /api/register` - Create new user account
- `POST /api/login` - User login

**Chat:**
- `POST /chat` - Send message (works with or without authentication)

**User Management:**
- `GET /api/sessions` - Get user's chat sessions (requires auth)
- `GET /api/sessions/<id>` - Get specific session (requires auth)
- `DELETE /api/sessions/<id>` - Delete session (requires auth)

**Analytics:**
- `GET /api/analytics` - Get user analytics (requires auth)
- `GET /api/status` - Get server status

**System:**
- `GET /api/health` - Health check

#### Authentication

To use authenticated features, include the API key in the Authorization header:
```bash
curl -H "Authorization: Bearer your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello!"}' \
     http://localhost:5000/chat
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | **Required** |
| `SECRET_KEY` | Flask secret key | Random generated |
| `DATABASE_URL` | SQLite database path | `chatbot.db` |
| `DEBUG` | Enable debug mode | `False` |
| `MAX_MESSAGE_LENGTH` | Maximum message length | `2000` |
| `MAX_SESSIONS_PER_USER` | Sessions per user | `50` |

### Rate Limiting

Default limits:
- **General**: 200 requests/day, 50 requests/hour
- **Chat**: 10 messages/minute

## 📊 Analytics Dashboard

The analytics dashboard provides insights into:

- **Usage Statistics**: Total sessions, messages, tokens used
- **User Activity**: Recent logins, message trends
- **Session Management**: Active sessions, message counts
- **Performance Metrics**: Response times, token usage

Access at: [http://localhost:5000/analytics](http://localhost:5000/analytics) (requires login)

## 🛠️ Development

### Running in Development Mode

```bash
python app.py
# or
python run_server.py dev
```

### Running in Production Mode

```bash
python run_server.py prod
# Uses Gunicorn with optimized settings
```

### Database Schema

The application uses SQLite with the following main tables:
- **users**: User accounts and API keys
- **chat_sessions**: Chat session management
- **messages**: Individual chat messages
- **analytics**: Usage tracking and events
- **api_usage**: API call logging

## 🔒 Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **API Key Authentication**: Secure token-based authentication
- **Rate Limiting**: Prevent abuse and ensure fair usage
- **Input Validation**: Sanitize and validate all user inputs
- **CORS Configuration**: Secure cross-origin requests

## 🚀 Deployment

For production deployment:

1. **Use a proper WSGI server** (Gunicorn is included)
2. **Set environment variables** securely
3. **Use a reverse proxy** (nginx recommended)
4. **Enable HTTPS** for security
5. **Configure proper logging** and monitoring

## 📝 Logging

The application provides comprehensive logging:
- **Application logs**: `chatbot_server.log`
- **Access logs**: `access.log` (in production mode)
- **Error logs**: `error.log` (in production mode)

View logs in the web interface: [http://localhost:5000/logs/view](http://localhost:5000/logs/view)

## 🤝 API Usage Examples

### Basic Chat (No Authentication)
```javascript
fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello!' })
})
.then(res => res.json())
.then(data => console.log(data.reply));
```

### Authenticated Chat
```javascript
fetch('/chat', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your_api_key'
  },
  body: JSON.stringify({ message: 'Hello!', session_id: 'session_123' })
})
.then(res => res.json())
.then(data => console.log(data.reply));
```

## 📋 Requirements

See `requirements.txt` for a complete list of dependencies. Main packages:

- **Flask**: Web framework
- **Groq**: AI model API client
- **Flask-CORS**: Cross-origin resource sharing
- **Flask-Limiter**: Rate limiting
- **Werkzeug**: Security utilities
- **python-dotenv**: Environment variable management
- **Gunicorn**: Production WSGI server (optional)

## 🎨 UI Themes

The application includes a modern dark theme with:
- **Responsive Design**: Works on desktop and mobile
- **Markdown Support**: Rich text formatting in messages
- **Syntax Highlighting**: Code block formatting
- **Real-time Indicators**: Typing indicators and status updates

## 🐛 Troubleshooting

### Common Issues

1. **"GROQ_API_KEY not found"**
   - Ensure `.env` file exists with your API key
   - Check the key is correctly formatted

2. **"Failed to fetch" errors**
   - Access via `http://localhost:5000`, not `file://` URLs
   - Check if the server is running
   - Verify CORS settings

3. **Database errors**
   - The database is created automatically
   - Check file permissions in the project directory

4. **Rate limit exceeded**
   - Wait for the rate limit to reset
   - Consider authentication for higher limits

## � Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the server logs for error details
3. Ensure all requirements are installed correctly
4. Verify your Groq API key is valid and has credits

## 🎯 Future Enhancements

Potential improvements and features:
- **File Upload Support**: Image and document processing
- **Multiple AI Models**: Support for different models
- **Real-time Chat**: WebSocket support for real-time features
- **Advanced Analytics**: More detailed usage insights
- **Plugin System**: Extensible functionality
- **Multi-language Support**: Internationalization

---

**Current Version**: Production v1.0  
**Model**: LLaMA 3.3 70B Versatile (Groq)  
**Last Updated**: July 2026
