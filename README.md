# LiveKit Voice AI - Medical Triage System

A professional voice AI application using LiveKit Agents v1.0 framework with FastAPI backend and multi-agent medical triage system.

## 🏗️ Project Structure

```
project/
├── app/                    # FastAPI application
│   ├── main.py            # Application entry point
│   └── api/
│       └── routes.py      # API endpoints for call management
├── agents/                # LiveKit AI agents
│   └── medical_triage.py  # Medical office triage system
├── static/                # Frontend files
│   └── index.html         # Web interface with voice integration
├── requirements.txt       # Python dependencies
├── run.py                # Development server runner
└── .env                  # Environment configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file with your API credentials:

```bash
# LiveKit Configuration (Required)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# AI Provider API Keys (Required)
OPENAI_API_KEY=your_openai_api_key           # For LLM
DEEPGRAM_API_KEY=your_deepgram_api_key       # For Speech-to-Text
CARTESIA_API_KEY=your_cartesia_api_key       # For Text-to-Speech

# Optional FastAPI Configuration
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
LOG_LEVEL=INFO
```

**Get Your API Keys:**

- **LiveKit**: Sign up at [livekit.io/cloud](https://livekit.io/cloud)
- **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com)
- **Deepgram**: Sign up at [deepgram.com](https://deepgram.com)
- **Cartesia**: Get API key from [cartesia.ai](https://cartesia.ai)

### 3. Download Required Model Files

```bash
python agents/medical_triage.py download-files
```

### 4. Install v1.0 Enhanced Features (Optional)

The code is designed to work with basic LiveKit Agents v1.0, but includes support for enhanced features:

```bash
# Install enhanced turn detection (recommended)
pip install "livekit-agents[turn-detector]"

# Install noise cancellation (optional)
pip install "livekit-agents[noise-cancellation]"
```

**Enhanced Features:**

- **🧠 Advanced Turn Detection**: Context-aware conversation flow using LiveKit's custom transformer model
- **🔇 Noise Cancellation**: Background noise and voice cancellation for clearer audio
- **📈 Better Interruption Handling**: Smarter detection of when users want to interrupt the agent

### 5. Start the Services

**This is now a microservices architecture. You need to run TWO services:**

#### Terminal 1: Start the Agent Worker

```bash
python run_agent.py dev
```

This starts the persistent agent worker that handles voice conversations.

#### Terminal 2: Start the API Service

```bash
python run.py
```

This starts the call creation API and web client at `http://localhost:8000`

### 6. Test the System

1. **API Testing**: Visit `http://localhost:8000` for API documentation
2. **Web Client**: Visit `http://localhost:8000/client` for voice testing
3. **Create a call via API**:
   ```bash
   curl -X POST "http://localhost:8000/calls/start" \
        -H "Content-Type: application/json" \
        -d '{"patient_name": "John Doe"}'
   ```
4. **Test voice connection**: Use the web client to join the created room

**Troubleshooting Voice Issues:**

- If you see "❌ Voice calls unavailable", use the diagnostic page: `http://localhost:8000/static/livekit-test.html`
- Check the browser console for detailed error messages
- Ensure your microphone permissions are enabled
- Test with a different browser if issues persist
- Verify your .env file has all required API keys configured

## 🏥 Medical Triage Agent Features

The v1.0 agent system includes:

### Multi-Agent Architecture

- **Triage Agent**: Initial patient assessment and routing
- **Support Agent**: Medical services and appointment assistance
- **Billing Agent**: Insurance and payment support

### Voice Capabilities

- Real-time speech-to-text with Deepgram
- Conversational AI with OpenAI GPT-4o-mini
- Natural text-to-speech with Cartesia
- Intelligent turn detection and interruption handling

### Conversation Flow

1. **Initial Greeting**: Agent welcomes patient professionally
2. **Information Collection**: Gathers name, symptoms, and urgency
3. **Smart Routing**: Transfers to appropriate department
4. **Contextual Handoff**: Maintains conversation context across agents

## 🔧 Running the Agent

The medical triage agent supports multiple modes:

### Development Mode (Recommended)

```bash
python run_agent.py dev
```

- Connects to LiveKit Cloud
- Hot reloading on file changes
- Available via web interface

### Console Mode (Testing)

```bash
python agents/medical_triage.py console
```

- Local terminal-only testing
- No LiveKit server required
- Good for initial testing

### Production Mode

```bash
python agents/medical_triage.py start
```

- Production-ready optimizations
- No hot reloading
- Stable for deployment

## 📡 API Usage

This service is designed to be called by other applications to create voice AI calls.

### Integration Example

```python
import httpx

# Create a call
response = httpx.post("http://localhost:8000/calls/start",
                     json={"patient_name": "Jane Smith"})
call_data = response.json()

# Get access token for your client to connect
token_response = httpx.post("http://localhost:8000/token",
                           json={
                               "room_name": call_data["room_name"],
                               "participant_name": "Jane Smith"
                           })
token_data = token_response.json()

# Use token_data["token"] and token_data["url"] in your client
```

### API Endpoints

#### Health & Status

- `GET /` - API documentation and service info
- `GET /health` - Service health status
- `GET /agents` - Available agent list

#### Call Management

- `POST /calls/start` - Start new medical triage call

  ```json
  {
    "patient_name": "John Doe" // optional
  }
  ```

- `GET /calls/{call_id}` - Get call status
- `POST /calls/{call_id}/end` - End specific call
- `GET /calls` - List all active/recent calls

#### Authentication

- `POST /token` - Create LiveKit room access token
  ```json
  {
    "room_name": "medical-abc123",
    "participant_name": "John Doe"
  }
  ```

## 🎤 Voice Integration

The frontend includes full WebRTC voice integration:

### Features

- **Real-time Audio**: Direct connection to agent via WebRTC
- **LiveKit Client**: Automatic loading and error handling
- **Voice Status**: Clear indicators for connection state
- **Audio Controls**: Connect/disconnect voice during calls

### Browser Requirements

- Modern browser with WebRTC support
- Microphone access permissions
- HTTPS (required for microphone in production)

## 🛠️ Development Tips

### Agent Development

- The v1.0 framework uses `AgentSession` for voice pipeline management
- Agents are simple classes with instructions and tools
- Use `@function_tool` decorator for agent capabilities
- Agent handoff returns new agent instances

### Debugging

- Use console mode for quick testing: `python agents/medical_triage.py console`
- Check logs in the web interface
- Enable debug logging with `LOG_LEVEL=DEBUG`

### Testing Voice

1. Start both FastAPI backend and agent in dev mode
2. Create a call via web interface
3. Join voice call to test real-time conversation
4. Check browser console for WebRTC debugging

## 🔒 Production Deployment

### Security Checklist

- [ ] Use environment-specific API keys
- [ ] Enable HTTPS for WebRTC microphone access
- [ ] Set proper CORS origins (not `*`)
- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Use secure LiveKit server configuration

### Performance

- [ ] Scale agent workers based on concurrent calls
- [ ] Monitor LiveKit room utilization
- [ ] Add health checks and monitoring
- [ ] Configure auto-scaling for peak loads

## 🎯 Advanced Features

### Multi-Agent Capabilities

The system demonstrates advanced patterns:

- **Contextual transfers**: Patient information persists across agents
- **Department routing**: Intelligent routing based on patient needs
- **Conversation continuity**: Seamless handoffs between specialized agents

### Extensibility

- Add new agent types by inheriting from `Agent`
- Extend `TriageUserData` for additional patient information
- Implement custom tools with `@function_tool`
- Connect to external systems (EHR, scheduling, etc.)

## 🆘 Troubleshooting

### Common Issues

**"LiveKit client not ready"**

- Check internet connection
- Verify LiveKit CDN accessibility
- Try refreshing the page

**"Failed to start agent"**

- Verify all API keys in `.env` file
- Check that model files are downloaded
- Ensure agent script path is correct

**"Voice connection failed"**

- Check microphone permissions
- Verify LiveKit URL and credentials
- Ensure HTTPS in production

**"Agent not responding"**

- Check API key quotas (OpenAI, Deepgram, Cartesia)
- Verify network connectivity to AI providers
- Check agent logs for errors

### Getting Help

- Check the [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- Join the [LiveKit Community Slack](https://livekit.io/join-slack)
- Review the agent logs and browser console for errors

## 📊 Next Steps

1. **Add more agent types**: Specialized medical departments
2. **Implement conversation memory**: Patient history across sessions
3. **Add analytics**: Call volume, conversation insights
4. **Phone integration**: SIP/telephony support for real phone calls
5. **EHR integration**: Connect to medical record systems
