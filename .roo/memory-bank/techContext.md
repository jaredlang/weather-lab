# Tech Context: Weather Lab

## Technology Stack

### Core Technologies

#### Python 3.11+
- **Primary Language:** All components written in Python
- **Type Hints:** Used throughout for clarity and IDE support
- **Async/Await:** Used for I/O operations (MCP client, file operations)

#### Google Agent Development Kit (ADK)
- **Framework:** Agent orchestration and tool management
- **Version:** Latest (installed via pip)
- **Key Classes:**
  - `Agent` - Individual agent definition
  - `SequentialAgent` - Sequential sub-agent execution
  - `ToolContext` - Tool invocation context
  - `CallbackContext` - Agent lifecycle callbacks

#### Model Context Protocol (MCP)
- **Purpose:** Agent-to-storage communication protocol
- **Transport:** Server-Sent Events (SSE) over HTTP
- **Client Library:** `mcp` Python package
- **Server Pattern:** Remote MCP server (not stdio)

### External APIs

#### OpenWeather API
- **Endpoint:** `https://api.openweathermap.org/data/2.5/weather`
- **Authentication:** API key (free tier)
- **Rate Limit:** 60 calls/minute
- **Data:** Current weather conditions (temp, humidity, wind, conditions)
- **Cache:** 15-minute TTL to reduce API calls

#### Google Gemini (LLM)
- **Purpose:** Generate conversational weather forecasts
- **Model:** Configurable via `MODEL` env var (e.g., `gemini-1.5-flash`)
- **Usage:** Text generation (3-4 sentence forecasts)
- **Optimization:** 30-minute forecast cache to reduce token usage

#### Google Text-to-Speech (TTS)
- **Purpose:** Convert text forecasts to audio
- **Format:** WAV audio files
- **Language Support:** Multi-language (en, es, ja, zh, etc.)
- **Optimization:** Conditional generation (only when requested)

### Data Storage

#### Google Cloud SQL
- **Database:** PostgreSQL 17
- **Instance Tiers:**
  - Development: `db-f1-micro` (~$7/month)
  - Production: `db-custom-2-7680` (~$130/month)
- **Connection:** Cloud SQL Connector (not direct TCP)
- **Features:**
  - Auto-scaling CPU
  - Automatic backups
  - High availability (production)

#### Local File Storage
- **Purpose:** Temporary audio/text files
- **Location:** `output/` directory (gitignored)
- **Cleanup:** Automatic removal after 7 days
- **Structure:** `output/{city}/forecast_{timestamp}.{txt,wav}`

### Web Framework (REST API)

#### FastAPI
- **Version:** Latest stable
- **Features Used:**
  - Path parameters: `/weather/{city}`
  - Query parameters: `?language=en&limit=10`
  - Pydantic models for validation
  - Automatic OpenAPI docs (`/docs`, `/redoc`)
  - CORS middleware for web clients
- **Server:** Uvicorn ASGI server

### HTTP Clients

#### `requests` (Synchronous)
- **Usage:** OpenWeather API calls
- **Pattern:** Session-based connection pooling
- **Timeout:** 10 seconds
- **Retry:** Exponential backoff decorator

#### `httpx` (Async)
- **Usage:** MCP client SSE connections
- **Pattern:** Async context managers
- **Timeout:** 30 seconds (MCP operations)

### Testing Framework

#### pytest
- **Version:** Latest stable
- **Plugins:**
  - `pytest-asyncio` - Async test support
  - `pytest-cov` - Coverage reporting
- **Test Structure:**
  - Unit tests: Mock external APIs
  - Integration tests: Real MCP server
  - Test fixtures in `conftest.py`

## Development Environment

### Operating System
- **Platform:** Windows 11
- **Shell:** PowerShell 7
- **Path:** `c:\source\ai.dev\weather-lab`

### Constraints
- ❌ **No Bash scripts** - Use PowerShell or Python
- ✅ **PowerShell scripts** - `.bat` and `.ps1` files
- ✅ **Python scripts** - Cross-platform where possible

### IDE
- **Primary:** Visual Studio Code
- **Extensions:** Python, Pylance, MCP tools
- **Workspace:** `c:\source\ai.dev\weather-lab`

### Version Control
- **System:** Git
- **Ignore:** `.gitignore` excludes:
  - `output/` - Generated files
  - `.env` - Secrets
  - `__pycache__/` - Python cache
  - `.adk/` - ADK runtime
  - `venv/` - Virtual environment

## Python Dependencies

### Production Dependencies

#### Agent Framework
```
google-adk - Google Agent Development Kit
python-dotenv - Environment variable loading
```

#### API Clients
```
requests - HTTP client (OpenWeather API)
httpx - Async HTTP client (MCP SSE)
```

#### MCP
```
mcp - Model Context Protocol client
```

#### Database
```
pg8000 - PostgreSQL driver (pure Python)
cloud-sql-python-connector - Cloud SQL connector
```

#### Web Framework (REST API)
```
fastapi - Web framework
uvicorn - ASGI server
pydantic - Data validation
```

#### Google Cloud
```
google-cloud-logging - Structured logging
google-auth - GCP authentication
```

### Development Dependencies
```
pytest - Testing framework
pytest-asyncio - Async test support
pytest-cov - Coverage reporting
```

## Environment Variables

### Required Variables

#### OpenWeather API
```bash
OPENWEATHER_API_KEY=your_api_key_here
```

#### Google Cloud (Agent)
```bash
MODEL=gemini-1.5-flash          # LLM model
OUTPUT_DIR=output               # Local file storage
```

#### Google Cloud (MCP Server & API)
```bash
GCP_PROJECT_ID=your-project-id
CLOUD_SQL_REGION=us-central1
CLOUD_SQL_INSTANCE=weather-forecasts
CLOUD_SQL_DB=weather
CLOUD_SQL_USER=postgres
CLOUD_SQL_PASSWORD=your-password
```

#### MCP Client
```bash
MCP_SERVER_URL=http://localhost:8080
# or for production:
# MCP_SERVER_URL=https://forecast-mcp-server-xxxxx.run.app
```

#### REST API (Optional)
```bash
API_TITLE=Weather Forecast API
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### Configuration Files
- `.env.example` - Template in each component directory
- `.env` - Actual secrets (gitignored)

## Project Structure

```
weather-lab/
├── .roo/                               # Cline memory bank
│   ├── rules/
│   │   └── rules.md                    # Cline's rules
│   └── memory-bank/                    # Memory bank files
├── weather_agent/                      # Main agent system
│   ├── agent.py                        # Root agent
│   ├── tools.py                        # Shared tools
│   ├── forecast_storage_client.py      # MCP client wrapper
│   ├── write_file.py                   # File I/O
│   ├── requirements.txt
│   ├── .env.example
│   ├── caching/                        # Caching layer
│   │   ├── api_call_cache.py           # OpenWeather cache
│   │   ├── forecast_cache.py           # Forecast cache
│   │   └── forecast_file_cleanup.py    # File cleanup
│   ├── sub_agents/
│   │   ├── forecast_writer/            # Text generation
│   │   │   ├── agent.py
│   │   │   └── tools/
│   │   │       └── get_current_weather.py
│   │   └── forecast_speaker/           # Audio generation
│   │       ├── agent.py
│   │       └── tools/
│   │           └── generate_audio.py
│   └── tests/                          # Agent tests
│       ├── test_agent_mcp_integration.py
│       ├── test_api_call_caching.py
│       ├── test_forecast_caching.py
│       └── test_forecast_storage_client.py
├── forecast_storage_mcp/               # MCP server
│   ├── server.py                       # SSE server
│   ├── schema.sql                      # DB schema
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile                      # Container config
│   ├── README.md
│   ├── DEPLOYMENT.md
│   ├── INTEGRATION_PLAN.md
│   ├── REMOTE_MCP_GUIDE.md
│   ├── tools/
│   │   ├── connection.py               # Cloud SQL connector
│   │   ├── forecast_operations.py      # CRUD operations
│   │   └── encoding.py                 # Text encoding
│   └── tests/                          # MCP server tests
│       ├── test_encoding.py
│       ├── test_mcp_operations.py
│       ├── test_mcp_server_connection.py
│       └── test_remote_mcp.py
├── forecast_api/                       # REST API
│   ├── main.py                         # FastAPI app
│   ├── config.py                       # Settings
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile                      # Container config
│   ├── README.md
│   ├── TESTING.md
│   ├── TEST_SUMMARY.md
│   ├── run_tests.bat                   # Windows test runner
│   ├── run_tests.sh                    # Unix test runner
│   ├── api/
│   │   ├── routes/
│   │   │   ├── weather.py              # Weather endpoints
│   │   │   ├── stats.py                # Statistics
│   │   │   └── health.py               # Health check
│   │   └── models/
│   │       └── responses.py            # Pydantic models
│   ├── core/
│   │   ├── database.py                 # DB wrapper
│   │   └── exceptions.py               # Custom errors
│   └── tests/                          # API tests
│       └── manual_test.py
├── output/                             # Generated files (gitignored)
└── .gitignore                          # Git ignore rules
```

## Build & Run Commands

### Weather Agent (Local)
```powershell
cd weather_agent
pip install -r requirements.txt
# Set environment variables in .env
# Run via Google ADK CLI or programmatically
```

### MCP Server (Local)
```powershell
cd forecast_storage_mcp
pip install -r requirements.txt
python server.py
# Server runs on http://localhost:8080
```

### REST API (Local)
```powershell
cd forecast_api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Docker Build (MCP Server)
```powershell
cd forecast_storage_mcp
docker build -t forecast-mcp-server .
docker run -p 8080:8080 --env-file .env forecast-mcp-server
```

### Docker Build (REST API)
```powershell
cd forecast_api
docker build -t weather-forecast-api .
docker run -p 8000:8000 --env-file .env weather-forecast-api
```

### Cloud Run Deployment (MCP Server)
```bash
cd forecast_storage_mcp
gcloud run deploy forecast-mcp-server \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=your-project \
  --allow-unauthenticated
```

### Cloud Run Deployment (REST API)
```bash
cd forecast_api
gcloud run deploy weather-forecast-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=your-project \
  --allow-unauthenticated
```

## Testing Commands

### Run All Tests
```powershell
# Weather Agent
cd weather_agent
pytest

# MCP Server
cd forecast_storage_mcp
pytest

# REST API
cd forecast_api
pytest
# or
.\run_tests.bat
```

### Run Specific Test
```powershell
pytest tests/test_forecast_storage_client.py
pytest tests/test_api_call_caching.py -v
```

### Run with Coverage
```powershell
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Manual Integration Test
```powershell
# Start servers first
# Then run:
cd forecast_api
python tests/manual_test.py
```

## Development Workflow

### 1. Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` file with secrets
3. Start MCP server: `python forecast_storage_mcp/server.py`
4. Run agent or API locally
5. Test with curl or Python client

### 2. Testing
1. Write unit tests with mocked external APIs
2. Write integration tests with real MCP server
3. Run `pytest` to validate
4. Check coverage: `pytest --cov`

### 3. Deployment
1. Build Docker image
2. Test locally with Docker
3. Push to GCP Artifact Registry
4. Deploy to Cloud Run
5. Update `MCP_SERVER_URL` for production

## Technical Constraints

### API Rate Limits
- OpenWeather: 60 calls/minute (free tier)
- Gemini: Model-dependent (high limits)
- Google TTS: High limits (pay per character)

### Database Limits
- Cloud SQL connections: 100 (db-f1-micro)
- Storage: 10GB (dev), 50GB+ (prod)
- Query timeout: 30 seconds

### Cloud Run Limits
- Memory: 512MB (default), up to 8GB
- CPU: 1 vCPU (default), up to 8
- Timeout: 300 seconds (5 minutes)
- Concurrency: 80 requests per instance

### File System
- Cloud Run: Ephemeral filesystem
- Local files lost on restart
- Use Cloud SQL for persistence

## Performance Targets

### Response Times
- Cached forecast: < 1 second
- New forecast (no audio): 3-5 seconds
- New forecast (with audio): 5-10 seconds
- REST API (cached): < 500ms

### Throughput
- Agent: 10-20 requests/minute
- MCP server: 100+ requests/minute
- REST API: 100+ requests/minute
- Database: 1000+ queries/minute

### Resource Usage
- Memory: < 256MB per component
- CPU: < 0.5 vCPU average
- Storage: < 1GB forecasts
- Bandwidth: < 10GB/month

## Monitoring & Logging

### Logging
- Google Cloud Logging for structured logs
- Python `logging` module
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics
- Cache hit rates
- Response latencies
- API call counts
- Error rates
- Storage usage

### Health Checks
- `/health` endpoint (REST API)
- `test_connection` tool (MCP)
- Database connectivity checks
- External API availability

## Security Best Practices

1. **Environment Variables:** Never commit `.env` files
2. **API Keys:** Rotate regularly
3. **Cloud SQL:** Use Cloud SQL Connector (not public IP)
4. **HTTPS:** Always use HTTPS in production
5. **Input Validation:** Sanitize all user inputs
6. **Rate Limiting:** Protect against abuse
7. **Least Privilege:** Minimal IAM permissions

## Cost Optimization

### Current Costs (Development)
- Cloud SQL (db-f1-micro): ~$7/month
- Cloud Run (MCP + API): ~$0 (within free tier)
- OpenWeather API: $0 (free tier)
- Gemini: ~$1-5/month (with caching)
- Google TTS: ~$1-3/month (conditional generation)
- **Total:** ~$10-15/month

### Production Scaling
- Cloud SQL (db-custom-2-7680): ~$130/month
- Cloud Run: ~$20-50/month (auto-scaling)
- Storage: ~$10/month
- APIs: ~$10-30/month
- **Total:** ~$170-220/month (1000s of requests/day)
