# System Patterns: Weather Lab

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                  (Chat, API Client, curl)                   │
└────────────────────┬────────────────────┬───────────────────┘
                     │                    │
                     │                    │
           ┌─────────▼──────────┐  ┌──────▼──────────┐
           │  Weather Agent     │  │  Forecast API   │
           │  (Google ADK)      │  │  (FastAPI)      │
           └─────────┬──────────┘  └──────┬──────────┘
                     │                    │
                     │ MCP (SSE)          │ Direct SQL
                     │                    │
           ┌─────────▼────────────────────▼──────────┐
           │    Forecast Storage MCP Server          │
           │         (Python SSE Server)             │
           └─────────┬───────────────────────────────┘
                     │
                     │ Cloud SQL Connector
                     │
           ┌─────────▼───────────┐
           │  Cloud SQL          │
           │  PostgreSQL         │
           │  (forecasts table)  │
           └─────────────────────┘
```

## Component Architecture

### 1. Weather Agent (weather_agent/)
**Purpose:** Orchestrate weather forecast generation and delivery

**Structure:**
```
weather_agent/
├── agent.py                    # Root agent orchestration
├── tools.py                    # Shared utility tools
├── forecast_storage_client.py  # MCP client wrapper
├── write_file.py               # File I/O utilities
├── caching/                    # Caching layer
│   ├── api_call_cache.py       # OpenWeather API cache (15 min TTL)
│   ├── forecast_cache.py       # Forecast cache integration
│   └── forecast_file_cleanup.py # Old file cleanup
└── sub_agents/
    ├── forecast_writer/        # Text generation sub-agent
    │   ├── agent.py
    │   └── tools/
    │       └── get_current_weather.py  # OpenWeather API client
    └── forecast_speaker/       # Audio generation sub-agent
        ├── agent.py
        └── tools/
            └── generate_audio.py       # Google TTS client
```

**Design Pattern:** Sequential Agent Pattern
- Root agent delegates to sequential sub-agents
- Each sub-agent specializes in one task
- State shared via session context

**Key Flow:**
1. Root agent checks Cloud SQL cache via MCP client
2. If cached: Skip sub-agents, return immediately
3. If not cached:
   - Delegate to `forecast_writer_agent` → generates text
   - Conditionally delegate to `forecast_speaker_agent` → generates audio
   - Upload results to Cloud SQL via MCP client
4. Background cleanup of old files

### 2. Forecast Storage MCP Server (forecast_storage_mcp/)
**Purpose:** MCP server for agent-to-storage communication

**Structure:**
```
forecast_storage_mcp/
├── server.py                   # SSE MCP server entry point
├── schema.sql                  # Database schema
├── tools/
│   ├── connection.py           # Cloud SQL connector
│   ├── forecast_operations.py  # CRUD operations
│   └── encoding.py             # Text encoding utilities
└── tests/                      # MCP server tests
```

**Design Pattern:** Model Context Protocol (MCP)
- SSE transport for remote communication
- Tools exposed: upload_forecast, get_cached_forecast, cleanup, stats, list, test_connection
- Stateless server design

**Key Features:**
- Binary storage (BYTEA) for text and audio
- Automatic encoding detection (utf-8/16/32)
- TTL-based expiration management
- Storage statistics and per-city breakdown

### 3. Forecast API (forecast_api/)
**Purpose:** REST API for external clients

**Structure:**
```
forecast_api/
├── main.py                     # FastAPI app entry point
├── config.py                   # Settings management
├── api/
│   ├── routes/
│   │   ├── weather.py          # GET /weather/{city}
│   │   ├── stats.py            # GET /stats
│   │   └── health.py           # GET /health
│   └── models/
│       └── responses.py        # Pydantic schemas
└── core/
    ├── database.py             # Database wrapper
    └── exceptions.py           # Custom exceptions
```

**Design Pattern:** REST API with Direct SQL
- Reuses connection code from MCP server
- No MCP overhead for API clients
- FastAPI auto-generates OpenAPI docs

**Key Endpoints:**
- `GET /weather/{city}?language=en` - Latest forecast
- `GET /weather/{city}/history` - Forecast history
- `GET /stats` - Storage statistics
- `GET /health` - Health check

## Key Design Patterns

### 1. Multi-Level Caching Strategy

```
┌──────────────────────────────────────────────┐
│ Level 1: API Call Cache (15 min)            │
│ - In-memory dictionary with TTL             │
│ - File: weather_agent/caching/api_call_cache.py
│ - Key: f"{city}_{units}"                    │
│ - Reduces OpenWeather API calls by 80%+     │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│ Level 2: Forecast Cache (30 min)            │
│ - Cloud SQL PostgreSQL                      │
│ - File: forecast_storage_mcp/tools/forecast_operations.py
│ - Key: city + language                      │
│ - Reduces LLM+TTS calls by 70%+             │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│ Level 3: File Cleanup (7 days)              │
│ - Background async task                     │
│ - File: weather_agent/caching/forecast_file_cleanup.py
│ - Prevents disk space issues                │
└──────────────────────────────────────────────┘
```

### 2. Conditional Execution Pattern

**Location:** [`weather_agent/agent.py:19-30`](weather_agent/agent.py:19-30)

```python
async def conditional_upload_forecast(callback_context):
    """Upload only if not from cache."""
    if callback_context.state.get("FORECAST_CACHED", False):
        return  # Skip upload for cached forecasts
    await upload_forecast_to_storage(callback_context)
```

**Benefits:**
- Avoids duplicate storage writes
- Reduces Cloud SQL write costs
- Faster response for cached requests

### 3. Remote MCP Pattern

**Location:** [`weather_agent/forecast_storage_client.py:31-92`](weather_agent/forecast_storage_client.py:31-92)

**Key Innovation:** Base64 audio encoding for remote compatibility
```python
# MCP server may be remote and can't access local files
audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

result = await _call_mcp_tool_remote("upload_forecast", {
    "audio_data": audio_base64  # Not a file path!
})
```

**Why:** Enables MCP server deployment on Cloud Run (no local filesystem access)

### 4. Error Handling & Retry Pattern

**Location:** [`weather_agent/caching/api_call_cache.py`](weather_agent/caching/api_call_cache.py)

**Strategy:**
- Retry transient failures (5xx errors, timeouts)
- Don't retry client errors (4xx)
- Exponential backoff: 1s → 2s → 4s
- Max 3 retries before failing

### 5. Session State Management

**Pattern:** Shared state dictionary across agent hierarchy

**Key State Variables:**
```python
state = {
    "CITY": str,                    # User's requested city
    "WEATHER_TYPE": str,            # Type of forecast
    "FORECAST_TIMESTAMP": str,      # ISO 8601 timestamp
    "FORECAST_TEXT": str,           # Generated text
    "FORECAST_AUDIO": str,          # Audio file path
    "FORECAST_TEXT_FILE": str,      # Text file path
    "FORECAST_CACHED": bool,        # Cache hit indicator
}
```

**Usage:** Passed via [`ToolContext`](weather_agent/agent.py:73-75) to all tools

## Critical Implementation Paths

### Path 1: Cached Forecast (Fast Path)
**Duration:** < 1 second

1. User asks for weather → Root agent
2. Root agent calls [`get_cached_forecast_from_storage()`](weather_agent/forecast_storage_client.py:159-198)
3. MCP client calls remote MCP server via SSE
4. MCP server queries Cloud SQL
5. If found: Decode text, write audio file, return
6. Root agent skips sub-agents entirely
7. Return to user immediately

### Path 2: New Forecast (Slow Path)
**Duration:** 5-10 seconds

1. User asks for weather → Root agent
2. Cache check returns `cached: false`
3. Root agent delegates to `weather_studio_team` (SequentialAgent)
4. `forecast_writer_agent`:
   - Calls [`get_current_weather()`](weather_agent/sub_agents/forecast_writer/tools/get_current_weather.py) (check cache first)
   - Generates LLM forecast (Gemini)
   - Stores in session state
   - Writes text file
5. `forecast_speaker_agent` (if audio requested):
   - Calls [`generate_audio()`](weather_agent/sub_agents/forecast_speaker/tools/generate_audio.py)
   - Google TTS generates WAV
   - Stores in session state
6. Root agent [`after_agent_callback`](weather_agent/agent.py:19-30):
   - Uploads to Cloud SQL via MCP
   - Background cleanup of old files
7. Return to user

### Path 3: REST API Request
**Duration:** < 500ms

1. Client: `GET /weather/chicago`
2. FastAPI router: [`weather.py:get_latest_forecast()`](forecast_api/api/routes/weather.py)
3. Database wrapper: Direct Cloud SQL query (no MCP overhead)
4. Decode text (utf-8/16/32), encode audio (base64)
5. Return JSON response with forecast + metadata

## Component Communication

### Agent → MCP Server (SSE Transport)
```python
# weather_agent/forecast_storage_client.py
async with sse_client(sse_url) as (read, write):
    async with ClientSession(read, write) as session:
        result = await session.call_tool(tool_name, arguments)
```

### API → Cloud SQL (Direct Connection)
```python
# forecast_api/core/database.py
# Reuses forecast_storage_mcp/tools/connection.py
connector = Connector()
conn = connector.connect(
    instance_connection_name,
    "pg8000",
    user="postgres",
    password=password,
    db=database
)
```

## Database Schema

**Table:** `forecasts`

**Key Fields:**
```sql
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    forecast_text BYTEA NOT NULL,        -- Binary text
    audio_data BYTEA,                    -- Binary audio
    forecast_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    text_bytes INTEGER NOT NULL,
    audio_bytes INTEGER,
    encoding VARCHAR(20) DEFAULT 'utf-8',
    language VARCHAR(10) DEFAULT 'en',
    locale VARCHAR(20) DEFAULT 'en-US',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_city_language ON forecasts(city, language);
CREATE INDEX idx_expires_at ON forecasts(expires_at);
```

**Key Design Decisions:**
1. **BYTEA for text**: Supports all unicode encodings
2. **expires_at index**: Fast cleanup queries
3. **city + language index**: Fast cache lookups
4. **JSONB metadata**: Flexible extension without schema changes

## Performance Optimizations

### 1. Connection Pooling
- Reuse HTTP connections to OpenWeather API
- Reuse Cloud SQL connections (via Cloud SQL Connector)

### 2. Async Cleanup
- Fire-and-forget cleanup task
- Doesn't block upload response
```python
asyncio.create_task(cleanup_old_forecast_files_async())
```

### 3. Conditional Audio Generation
- Only generate when user explicitly requests
- Saves 50-70% of TTS costs

### 4. Direct SQL for REST API
- Bypass MCP protocol overhead
- < 100ms query time vs 200-300ms via MCP

## Testing Strategy

### Unit Tests
- Mock external APIs (OpenWeather, Google TTS)
- Test each tool independently
- Validate caching logic

### Integration Tests
- Test full agent flow with real MCP server
- Test REST API endpoints with test database
- Validate encoding/decoding pipelines

### Load Tests
- 60 requests/minute (API rate limit)
- Cache hit rate measurement
- Response time percentiles (p50, p95, p99)

## Deployment Architecture

```
┌──────────────────────────────────────────┐
│  Cloud Run Service: forecast-mcp-server │
│  - MCP SSE server                        │
│  - Public endpoint                       │
│  - Auto-scaling (0-10 instances)         │
└──────────────┬───────────────────────────┘
               │
               │ Cloud SQL Connector
               │
┌──────────────▼───────────────────────────┐
│  Cloud SQL Instance: weather-forecasts   │
│  - PostgreSQL 17                         │
│  - db-f1-micro (dev) / custom (prod)     │
│  - Auto-scaling CPU                      │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Cloud Run Service: weather-forecast-api │
│  - FastAPI REST API                      │
│  - Public endpoint                       │
│  - Auto-scaling (0-10 instances)         │
│  - Direct SQL connection                 │
└──────────────┬───────────────────────────┘
               │
               │ Cloud SQL Connector
               │
               └──────── (same Cloud SQL) ◀──┘
```

## Security Considerations

1. **API Keys:** Stored in environment variables, never committed
2. **Cloud SQL:** Password-protected, Cloud SQL Connector for auth
3. **CORS:** Configured for REST API, MCP server internal only
4. **Input Validation:** Pydantic models for API, parameter validation in tools
5. **Rate Limiting:** Protect against quota exhaustion
