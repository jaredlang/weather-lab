# System Patterns: Weather Lab

## Architecture Overview

### Multi-Agent Hierarchy
```
root_agent (weather_agent)
├── Tool: get_forecast_from_cache
├── Tool: cache_forecast
├── Tool: get_cache_stats
├── Tool: set_session_value
├── Tool: get_current_timestamp
└── Sub-Agent: weather_studio_team (SequentialAgent)
    ├── forecast_writer_agent
    │   ├── Tool: get_current_weather
    │   ├── Tool: set_session_value
    │   └── Tool: write_text_file
    └── forecast_speaker_agent
        ├── Tool: generate_audio
        └── Tool: set_session_value
```

## Key Design Patterns

### 1. Sequential Agent Pattern
**Location**: [`weather_agent/agent.py:13-20`](../../weather_agent/agent.py#L13-L20)

The `weather_studio_team` uses SequentialAgent to ensure ordered execution:
- First: `forecast_writer_agent` generates text forecast
- Then: `forecast_speaker_agent` converts to audio

**Trade-off**: Always executes both agents. Future optimization: conditional audio generation by attaching agents directly to root_agent.

### 2. Session State Pattern
**Files**: 
- [`weather_agent/tools.py`](../../weather_agent/tools.py)
- All agent instructions reference `{CITY}`, `{WEATHER_TYPE}`, `{FORECAST}`, etc.

**How it works**:
- `ToolContext.state` is a shared dictionary across agents
- Root agent stores: `CITY`, `WEATHER_TYPE`, `FORECAST_TIMESTAMP`
- Sub-agents read from and write to this shared state
- Session persists across tool calls within same conversation

**Critical Keys**:
- `CITY`: User's requested city
- `WEATHER_TYPE`: Type of forecast (defaults to "current weather condition")
- `FORECAST_TIMESTAMP`: Generated once, used in filenames
- `FORECAST`: Text forecast content
- `FORECAST_TEXT_FILE`: Path to saved text file
- `FORECAST_AUDIO`: Path to saved audio file

### 3. Two-Level Caching Strategy

#### Level 1: Weather API Cache (15 minutes)
**File**: [`weather_agent/api_call_cache.py`](../../weather_agent/api_call_cache.py)

**Implementation**:
```python
@cached_with_ttl(ttl=900)  # 15 minutes
def get_current_weather(city: str, units: str = "imperial"):
    # API call to OpenWeather
```

**Pattern**: TTLCache class with decorator
- In-memory cache: `{cache_key: (value, timestamp)}`
- Auto-expiration on get() if TTL exceeded
- Cache key: `f"{func_name}:{args}:{kwargs}"`

**Why 15 minutes**: Weather updates every 10-30 minutes, balancing freshness vs cost

#### Level 2: Complete Forecast Cache (30 minutes)
**File**: [`weather_agent/forecast_cache.py`](../../weather_agent/forecast_cache.py)

**Implementation**: Filesystem-based
- Scans `output/{city}/` for matching text + audio files
- Parses timestamps from filenames: `forecast_text_2025-12-25_143022.txt`
- Returns cached if both files exist and age < 30 minutes
- No in-memory state → survives restarts

**Why 30 minutes**: Complete forecasts change less frequently, LLM generation is expensive

### 4. Filesystem as Source of Truth

**Directory Structure**:
```
output/
└── {city_name}/
    ├── forecast_text_{timestamp}.txt
    └── forecast_audio_{timestamp}.wav
```

**Timestamp Format**: `YYYY-MM-DD_HHMMSS` (e.g., `2025-12-25_143022`)

**Benefits**:
- Persistent across restarts
- Easy to debug and inspect
- No database complexity
- Cache cleanup is just file deletion

**File Operations**:
- Created by: [`forecast_writer_agent`](../../weather_agent/sub_agents/forecast_writer/agent.py#L14-L38) (text), [`forecast_speaker_agent`](../../weather_agent/sub_agents/forecast_speaker/agent.py#L25) (audio)
- Read by: [`get_forecast_from_cache()`](../../weather_agent/forecast_cache.py#L86)
- Cleaned by: `cleanup_expired()` (future enhancement)

## Critical Implementation Paths

### Path 1: Cache Hit (Fast Path)
1. User asks: "What's the weather in Seattle?"
2. Root agent extracts `city="Seattle"`, stores in session
3. Root agent calls `get_forecast_from_cache(city="Seattle")`
4. Filesystem check finds valid files (age < 30 min)
5. Reads text content, returns paths
6. Root agent stores in session: `FORECAST`, `FORECAST_TEXT_FILE`, `FORECAST_AUDIO`
7. **SKIP weather_studio_team entirely**
8. Return result to user (< 2 seconds)

**Key Decision Point**: Line 43 in [`agent.py`](../../weather_agent/agent.py#L43)
> "If cached is True... SKIP calling weather_studio_team entirely"

### Path 2: Cache Miss (Slow Path)
1. User asks: "What's the weather in Paris?"
2. Root agent extracts `city="Paris"`, stores in session
3. Root agent calls `get_forecast_from_cache(city="Paris")`
4. No valid cache found → `cached=False`
5. Root agent delegates to `weather_studio_team`
6. **forecast_writer_agent**:
   - Calls `get_current_weather(city="Paris")` → might hit Level 1 cache (15 min)
   - Generates text forecast using LLM
   - Stores in session as `FORECAST`
   - Writes to file, stores path as `FORECAST_TEXT_FILE`
7. **forecast_speaker_agent**:
   - Reads `FORECAST` from session
   - Generates audio via Gemini TTS
   - Writes to file, stores path as `FORECAST_AUDIO`
8. Root agent calls `cache_forecast()` to confirm files exist
9. Return result to user (5-15 seconds)

### Path 3: Weather API Cache Hit (Medium Path)
1. Two users ask about same city within 15 minutes
2. First user: Full slow path (cache miss)
3. Second user: 
   - Level 2 cache miss (different timestamp or > 30 min)
   - Delegates to weather_studio_team
   - **Level 1 cache hit**: `get_current_weather()` returns cached data instantly
   - Skips OpenWeather API call
   - Still generates new LLM forecast + audio
   - Saves new files with new timestamp
4. Return result (8-12 seconds - saved weather API call only)

## Component Relationships

### Root Agent → Sub-Agents Communication
**Method**: Session state (`tool_context.state`)
- Root writes: `CITY`, `WEATHER_TYPE`, `FORECAST_TIMESTAMP`
- Sub-agents read these values
- Sub-agents write: `FORECAST`, `FORECAST_TEXT_FILE`, `FORECAST_AUDIO`
- Root reads back results

**No direct return values**: Agents communicate only through session state

### Tool → Agent Communication
**Method**: Return dictionaries
```python
def get_current_weather(city: str) -> Dict[str, Any]:
    return formatted_string  # Actually returns string for this tool

def write_text_file(tool_context: ToolContext, city_name: str) -> Dict[str, str]:
    return {"status": "success", "file_path": file_path}
```

### API Integrations
1. **OpenWeather API**
   - Endpoint: `https://api.openweathermap.org/data/2.5/weather`
   - Auth: API key in query params
   - Rate limit: 60 calls/minute (free tier)
   - Implementation: [`get_current_weather.py`](../../weather_agent/sub_agents/forecast_writer/tools/get_current_weather.py)

2. **Google Gemini TTS**
   - SDK: `google.genai.Client()`
   - Model: Specified in `TTS_MODEL` env var
   - Voice: 'Kore' (prebuilt)
   - Output: PCM audio data → saved as WAV
   - Implementation: [`generate_audio.py`](../../weather_agent/sub_agents/forecast_speaker/tools/generate_audio.py)

## Error Handling Patterns

### Current State (Basic)
1. **API Errors**: Try/except in [`get_current_weather.py:72-76`](../../weather_agent/sub_agents/forecast_writer/tools/get_current_weather.py#L72-L76)
   - Returns error dict instead of raising
   - Agent can see error and inform user

2. **File Errors**: Try/except in [`forecast_cache.py:176-180`](../../weather_agent/forecast_cache.py#L176-L180)
   - Returns None if file read fails
   - Graceful degradation

### Missing (From improvement-plan.md)
- No retry logic with exponential backoff
- No timeouts on HTTP requests
- No connection pooling
- No rate limiting protection

## Performance Characteristics

### Current Timings (Estimated)
- **Cache hit**: 1-2 seconds (file I/O only)
- **API cache hit, forecast miss**: 8-12 seconds (LLM + TTS, skip API)
- **Complete miss**: 12-18 seconds (API + LLM + TTS)
- **OpenWeather API call**: 200-500ms
- **LLM forecast generation**: 2-4 seconds
- **TTS audio generation**: 3-8 seconds

### Bottlenecks (Identified)
1. **TTS is slowest** (3-8 sec) → conditional generation highest priority
2. **Sequential execution** → can't parallelize text/audio (ADK limitation)
3. **No async/await** → blocking I/O operations
4. **Redundant API calls** → partially solved by Level 1 cache

## Data Flow Diagram

```
User Query
    ↓
[Root Agent]
    ↓
Check Level 2 Cache (Filesystem)
    ↓
    ├── Cache Hit → Return (1-2s)
    ↓
    └── Cache Miss
        ↓
    [weather_studio_team]
        ↓
    [forecast_writer_agent]
        ↓
    Check Level 1 Cache (Memory)
        ↓
        ├── Cache Hit → Skip API call
        ↓
        └── Cache Miss → OpenWeather API (200-500ms)
        ↓
    Generate Text Forecast (LLM: 2-4s)
        ↓
    Write Text File
        ↓
    [forecast_speaker_agent]
        ↓
    Generate Audio (TTS: 3-8s)
        ↓
    Write Audio File
        ↓
    [Root Agent]
        ↓
    Confirm Cache
        ↓
    Return to User (12-18s)
```

## Configuration Points

### Environment Variables
```
MODEL=gemini-2.0-flash-exp
TTS_MODEL=gemini-2.0-flash-exp
OPENWEATHER_API_KEY={key}
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5/weather
OUTPUT_DIR=output
AGENT_ENGINE_ID=projects/{id}/locations/{loc}/reasoningEngines/{id}
```

### Tunable Parameters
- API cache TTL: 900s (15 min) - [`api_call_cache.py:47`](../../weather_agent/api_call_cache.py#L47)
- Forecast cache TTL: 1800s (30 min) - [`forecast_cache.py:29`](../../weather_agent/forecast_cache.py#L29)
- Timestamp format: `%Y-%m-%d_%H%M%S` - [`tools.py:13`](../../weather_agent/tools.py#L13)
- Audio voice: 'Kore' - [`generate_audio.py:47`](../../weather_agent/sub_agents/forecast_speaker/tools/generate_audio.py#L47)
- Default units: "imperial" - [`get_current_weather.py:48`](../../weather_agent/sub_agents/forecast_writer/tools/get_current_weather.py#L48)

## Testing Patterns

### Current Test Files
- [`test_api_call_caching.py`](../../test_api_call_caching.py) - Tests Level 1 cache
- [`test_forecast_caching.py`](../../test_forecast_caching.py) - Tests Level 2 cache

### Test Strategy
1. Unit test individual tools
2. Test cache TTL expiration
3. Test cache key generation
4. Test filesystem operations
5. Integration test: Full agent flow
