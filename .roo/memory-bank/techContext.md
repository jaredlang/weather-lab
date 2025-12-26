# Tech Context: Weather Lab

## Technology Stack

### Core Framework
**Google Agent Development Kit (ADK)**
- Version: Latest (via `google-cloud-aiplatform[adk,agent_engines]`)
- Purpose: Multi-agent orchestration framework
- Key Classes:
  - `Agent`: Individual agent with instructions, tools, and model
  - `SequentialAgent`: Executes sub-agents in sequence
  - `ToolContext`: Shared session state between agents
- Deployment: Vertex AI Reasoning Engines

### Language Models
**Google Gemini**
- **Text Generation**: `gemini-2.0-flash-exp`
  - Used for: Weather forecast text generation
  - Context: 3-4 sentence conversational forecasts
- **Text-to-Speech**: `gemini-2.0-flash-exp`
  - Used for: Audio forecast generation
  - Voice: 'Kore' (prebuilt voice config)
  - Output format: PCM audio → WAV files (24kHz, mono, 16-bit)

### External APIs
**OpenWeather API**
- Endpoint: `https://api.openweathermap.org/data/2.5/weather`
- Authentication: API key (query parameter)
- Rate Limit: 60 calls/minute (free tier)
- Response: JSON with weather data
- Units: Imperial (°F, mph) or Metric (°C, m/s)

### Python Version & Dependencies
**Python**: 3.10+ (required for Google ADK)

**Core Dependencies** ([`requirements.txt`](../../requirements.txt)):
```
google-cloud-aiplatform[adk,agent_engines]  # Google ADK framework
requests                                     # HTTP client for OpenWeather API
python-dotenv                                # Environment variable management
streamlit                                    # Web UI
# chainlit                                   # Alternative web UI (commented)
```

### UI Frameworks

#### Streamlit
**File**: [`streamlit_ui/app.py`](../../streamlit_ui/app.py)
- **Purpose**: Primary web interface
- **Features**:
  - Chat-based interaction
  - Session persistence (saves to JSON file)
  - Clear chat history button
  - Message streaming from agent
- **Session Management**: 
  - User ID: `user_123` (hardcoded)
  - Session ID from Vertex AI agent_engines
  - Chat history saved to `streamlit_ui/chat_history/chat_history.json`

#### Chainlit
**File**: [`chainlit_ui/app.py`](../../chainlit_ui/app.py)
- **Purpose**: Alternative web interface
- **Features**:
  - Starter prompts (pre-defined queries)
  - Real-time message streaming
  - Welcome message on chat start
- **Status**: Commented out in requirements.txt (not actively used)

## Development Environment

### Project Structure
```
weather-lab/
├── .venv/                      # Virtual environment
├── .roo/                       # Roo AI configuration
│   ├── rules/                  # Custom rules
│   └── memory-bank/            # This directory
├── weather_agent/              # Core agent system
│   ├── __init__.py
│   ├── agent.py               # Root agent
│   ├── server.py              # Empty (future deployment?)
│   ├── tools.py               # Shared utility tools
│   ├── api_call_cache.py      # Level 1 caching
│   ├── forecast_cache.py      # Level 2 caching
│   ├── improvement-plan.md    # Optimization roadmap
│   └── sub_agents/
│       ├── forecast_writer/   # Text forecast generation
│       │   ├── agent.py
│       │   └── tools/
│       │       └── get_current_weather.py
│       └── forecast_speaker/  # Audio generation
│           ├── agent.py
│           └── tools/
│               └── generate_audio.py
├── streamlit_ui/              # Streamlit interface
│   ├── app.py
│   ├── Dockerfile             # Container deployment
│   ├── .gitignore
│   └── chat_history/          # Persisted sessions
├── chainlit_ui/               # Chainlit interface
│   ├── app.py
│   └── chainlit.md
├── database_mcp/              # MCP server (empty)
├── output/                    # Generated forecasts (gitignored)
│   └── {city}/
│       ├── forecast_text_*.txt
│       └── forecast_audio_*.wav
├── .gitignore
├── requirements.txt
├── test_api_call_caching.py   # Unit tests
└── test_forecast_caching.py   # Unit tests
```

### Environment Configuration
**File**: `.env` (not tracked in git)

Required variables:
```bash
# Google Cloud / Vertex AI
MODEL=gemini-2.0-flash-exp
TTS_MODEL=gemini-2.0-flash-exp
AGENT_ENGINE_ID=projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}

# OpenWeather API
OPENWEATHER_API_KEY={your_api_key}
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5/weather

# File Output
OUTPUT_DIR=output
```

### Local Development Setup
1. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   - Copy `.env.example` to `.env` (if exists)
   - Add API keys and project IDs

4. **Run Streamlit UI**:
   ```bash
   cd streamlit_ui
   streamlit run app.py
   ```

5. **Run Chainlit UI**:
   ```bash
   cd chainlit_ui
   chainlit run app.py
   ```

## Technical Constraints

### Google ADK Limitations
1. **Synchronous Only**: No native async/await support
   - All operations are blocking
   - Cannot parallelize text and audio generation
   - Sequential execution required

2. **Session State**: Only `ToolContext.state` for agent communication
   - No direct return values from sub-agents
   - All data must flow through session dictionary
   - State persists only during single conversation

3. **Tool Function Signatures**: Must accept `ToolContext` as first param
   - Example: `def tool(tool_context: ToolContext, arg1: str) -> Dict[str, Any]`

### File System Requirements
- Write permissions in `OUTPUT_DIR` (default: `./output/`)
- Persistent storage for forecast caching
- Cleanup strategy needed (files accumulate over time)

### API Rate Limits
**OpenWeather Free Tier**:
- 60 calls/minute
- 1,000 calls/day
- No rate limiting implemented yet (see improvement-plan.md)

**Google Gemini**:
- Rate limits depend on project quota
- TTS calls can be expensive in high-volume scenarios

### Network Dependencies
- Internet connection required for:
  - OpenWeather API calls
  - Google Gemini LLM calls
  - Google Gemini TTS calls
- No offline mode available

## Deployment Considerations

### Vertex AI Deployment
**Agent Engine ID**: Retrieved via Vertex AI console or CLI
- Format: `projects/{id}/locations/{location}/reasoningEngines/{engine_id}`
- Used by UI apps to connect to deployed agent

### Docker Support
**File**: [`streamlit_ui/Dockerfile`](../../streamlit_ui/Dockerfile)
- Containerization support for Streamlit UI
- Can deploy to Cloud Run, GKE, or other container platforms

### State Persistence
**Streamlit**: Chat history saved to JSON file
- Path: `streamlit_ui/chat_history/chat_history.json`
- Survives application restarts
- Single user assumed (`user_123`)

**Agent Session**: Managed by Vertex AI
- Session ID from `agent.create_session(user_id)`
- State persists during conversation
- New session = fresh state

## Development Tools

### Testing
- **Unit Tests**: `test_api_call_caching.py`, `test_forecast_caching.py`
- **Manual Testing**: Use Streamlit/Chainlit UIs
- **Cache Inspection**: Check `output/` directory for files

### Debugging
1. **Print Statements**: Scattered throughout for event tracking
   - Streamlit: `print("*** EVENT *** ", event)`
   - Chainlit: `print(event)`, `print(part)`
2. **File Inspection**: Check generated `.txt` and `.wav` files
3. **Cache Debugging**: Use `get_cache_stats()` tool
4. **Session State**: Print `tool_context.state` in tools

### Git Ignore Patterns
From [`.gitignore`](../../.gitignore):
- `.venv/` - Virtual environment
- `output/` - Generated forecasts
- `.env` - Secrets
- `__pycache__/`, `*.pyc` - Python bytecode
- `chat_history/` - Streamlit sessions

## Performance Characteristics

### Caching Strategy Impact
| Scenario | Weather API | LLM | TTS | Total Time |
|----------|-------------|-----|-----|------------|
| Level 2 Cache Hit | ✗ Skip | ✗ Skip | ✗ Skip | 1-2s |
| Level 1 Cache Hit | ✗ Skip | ✓ Generate | ✓ Generate | 8-12s |
| Complete Miss | ✓ Call | ✓ Generate | ✓ Generate | 12-18s |

### Memory Usage
- **In-Memory Cache**: Minimal (Level 1 cache for weather data)
- **File System**: Grows over time (needs cleanup strategy)
- **Session State**: Small dictionary per conversation

### Scalability
**Current Limitations**:
- Single-threaded Python application
- No load balancing
- File system cache not distributed
- Hardcoded user ID in UIs

**Scale Considerations**:
- Multiple instances = separate file caches (inefficient)
- Need Redis/Memcached for distributed caching
- Database for session management at scale

## Known Technical Debt

From [`improvement-plan.md`](../../weather_agent/improvement-plan.md):

1. **No Retry Logic**: Single-attempt API calls can fail
2. **No Timeouts**: Requests can hang indefinitely
3. **No Connection Pooling**: New TCP connection per API call
4. **No Rate Limiting**: Risk of hitting OpenWeather quotas
5. **Synchronous I/O**: Blocking file writes and HTTP requests
6. **Always Generates Audio**: Even when user doesn't need it
7. **No Monitoring**: No metrics on cache hit rates, latencies, errors
8. **No File Cleanup**: Output directory grows unbounded

## Security Considerations

### API Key Management
- ✅ Keys stored in `.env` (not in git)
- ✅ Loaded via `python-dotenv`
- ⚠️ No key rotation mechanism
- ⚠️ No secrets manager integration (e.g., Google Secret Manager)

### User Data
- No authentication system
- Hardcoded user ID (`user_123`)
- Chat history stored locally (not encrypted)
- No PII handling considerations

### Network Security
- All API calls over HTTPS
- No request signing beyond API keys
- No input validation on city names (potential injection risks)

## Future Technical Improvements

1. **Async/Await**: If ADK adds support, refactor for async
2. **Distributed Cache**: Redis for multi-instance deployments
3. **Database**: PostgreSQL for session management
4. **Monitoring**: Prometheus/Grafana for metrics
5. **Authentication**: Add OAuth2 for multi-user support
6. **MCP Server**: Complete `database_mcp/` for external data access
