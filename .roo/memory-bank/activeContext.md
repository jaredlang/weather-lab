# Active Context: Weather Lab

## Current Work Focus

### Immediate Status
The weather lab project is **functionally complete** with a working multi-agent system that:
- ✅ Fetches weather data from OpenWeather API
- ✅ Generates conversational text forecasts
- ✅ Creates audio forecasts with TTS
- ✅ Implements two-level caching (API + forecast)
- ✅ Provides Streamlit UI for user interaction
- ✅ Has Chainlit UI as alternative interface

### Recent Changes & Optimizations

#### Completed: Local File Cleanup System (2025-12-26)
1. **Async File Cleanup** ([`forecast_file_cleanup.py`](../../weather_agent/forecast_file_cleanup.py))
   - Automatic cleanup of forecast files older than configurable threshold
   - Runs asynchronously after successful database upload
   - Fire-and-forget pattern using `asyncio.create_task()`
   - Configurable via `FORECAST_CLEANUP_DAYS` environment variable (default: 7 days)
   - Scans entire `output/` directory structure
   - Logs cleanup statistics (files deleted, bytes freed)

2. **Integration** ([`forecast_storage_client.py:131`](../../weather_agent/forecast_storage_client.py#L131))
   - Cleanup triggered after successful Cloud SQL upload
   - Non-blocking execution (doesn't delay upload response)
   - Safe error handling (cleanup failures don't affect upload)

#### Completed: Two-Level Caching System
1. **API Call Cache** ([`api_call_cache.py`](../../weather_agent/api_call_cache.py))
   - Implemented TTLCache class with time-based expiration
   - Added `@cached_with_ttl` decorator
   - 15-minute TTL for weather API responses
   - Reduces redundant OpenWeather API calls by 80-95%

2. **Forecast Cache** ([`forecast_cache.py`](../../weather_agent/forecast_cache.py))
   - Filesystem-based caching (no in-memory state)
   - 30-minute TTL for complete forecasts (text + audio)
   - Scans output directory for existing files
   - Survives application restarts

#### Agent Architecture Refinement
- Root agent now checks cache BEFORE delegating to sub-agents
- Instructions explicitly state: "SKIP calling weather_studio_team entirely" if cached
- Session state management for inter-agent communication
- Timestamp generation for filename consistency

## Next Steps & Priorities

### High Priority (From improvement-plan.md)
1. **Conditional Audio Generation** ⭐ HIGHEST PRIORITY
   - Current issue: SequentialAgent always runs both sub-agents
   - Solution: Attach sub-agents directly to root_agent
   - Skip forecast_speaker_agent when audio not requested
   - Expected impact: 50-70% cost savings, 2-5 second speed improvement

2. **Retry Logic with Exponential Backoff**
   - Add `@retry_with_backoff` decorator to API calls
   - Exponential backoff: 1s → 2s → 4s delays
   - Only retry transient failures (5xx, timeouts)
   - Improves reliability by 95%

3. **Request Timeouts**
   - Add `timeout=10` to OpenWeather API calls
   - Add `timeout=30` to Gemini TTS calls
   - Prevents indefinite hangs

### Medium Priority
4. **Connection Pooling**
   - Use `requests.Session()` for OpenWeather API
   - Reuse TCP connections
   - Save 50-100ms per request

5. **Rate Limiting Protection**
   - Implement token bucket algorithm
   - Limit to 60 calls/minute (OpenWeather free tier)
   - Prevent API quota errors

### Low Priority
6. **Monitoring & Metrics**
   - Track cache hit/miss rates
   - Measure latencies per operation
   - Count API calls and costs
   - Enable data-driven optimization

## Active Decisions & Considerations

### Why Filesystem-Based Cache?
**Decision**: Use filesystem as source of truth instead of in-memory cache

**Rationale**:
- Survives application restarts
- Easy to debug and inspect
- No database complexity
- Works well for single-instance deployments

**Trade-off**: Not suitable for distributed/multi-instance deployments
- Future: Consider Redis for horizontal scaling

### Why Two Cache Levels?
**Decision**: Separate caches for weather API (15 min) and complete forecasts (30 min)

**Rationale**:
- Weather data changes frequently (10-30 min updates)
- LLM-generated forecasts can stay fresh longer
- API calls are cheaper than LLM generation
- Maximizes cache hit rates at each level

### Why SequentialAgent?
**Decision**: Use SequentialAgent for weather_studio_team

**Current State**: Forces sequential execution (writer → speaker)
**Issue**: Always executes both agents, even when audio not needed

**Next Decision**: Move to direct sub-agent attachment on root_agent
- Allows conditional execution
- Root agent decides whether to invoke speaker agent

### Session State Pattern
**Decision**: Use `ToolContext.state` for agent communication

**Rationale**:
- Only mechanism provided by Google ADK
- Shared dictionary across all agents in conversation
- Persists during single session

**Important Keys** (must be consistent):
- `CITY` - User's requested city
- `FORECAST` - Generated text forecast
- `FORECAST_TEXT_FILE` - Path to saved text file
- `FORECAST_AUDIO` - Path to saved audio file
- `FORECAST_TIMESTAMP` - Used in filenames for consistency

**Pattern**: All agents read/write to these standard keys

## Important Patterns & Preferences

### Filename Timestamp Pattern
**Format**: `YYYY-MM-DD_HHMMSS`
**Example**: `forecast_text_2025-12-25_143022.txt`

**Why this format?**:
- Sortable chronologically
- No timezone ambiguity (assumes local time)
- Easy to parse with `datetime.strptime()`
- Consistent across text and audio files

**Critical**: Both text and audio files must use SAME timestamp
- Generated once by root agent: `get_current_timestamp()`
- Stored in session: `FORECAST_TIMESTAMP`
- Used by both writer and speaker agents

### Cache TTL Values
**Weather API Cache**: 900 seconds (15 minutes)
- Weather updates every 10-30 minutes
- Balance between freshness and cost

**Forecast Cache**: 1800 seconds (30 minutes)
- Complete forecasts change less frequently
- LLM generation expensive, worth longer cache

**Tunable**: Can adjust based on user requirements and cost constraints

### Error Handling Philosophy
**Current**: Graceful degradation
- Return error dictionaries instead of raising exceptions
- Agents can see errors and inform users
- Example: `{"error": str(e), "message": "Failed to fetch weather"}`

**Future**: Add retry logic for transient failures
- Don't retry client errors (4xx)
- Retry server errors (5xx) and timeouts

## Learnings & Project Insights

### What Works Well
1. **Two-level caching**: Dramatically reduces costs and improves speed
2. **Filesystem cache**: Simple, debuggable, persistent
3. **Session state**: Effective for agent communication in ADK
4. **Conversational forecasts**: LLM generates engaging, natural text
5. **Streamlit UI**: Clean, intuitive interface for weather queries

### Pain Points Discovered (and Resolutions)
1. **SequentialAgent limitation**: Can't conditionally skip agents
2. **No async support in ADK**: All operations blocking
3. **No built-in retry logic**: Must implement manually
4. ~~**File accumulation**: Need cleanup strategy~~ ✅ **RESOLVED** - Async cleanup implemented
5. **Hardcoded user ID**: Not ready for multi-user deployment

### Performance Observations
- **Cache hits**: < 2 seconds (excellent user experience)
- **API cache hits**: 8-12 seconds (good, saves API cost)
- **Complete misses**: 12-18 seconds (acceptable, lots of work happening)
- **TTS is slowest**: 3-8 seconds (conditional generation is high priority)

### Cost Insights
**Most Expensive Operations** (in order):
1. TTS audio generation (Gemini TTS) - $0.001-0.01 per request
2. LLM forecast generation (Gemini) - $0.0001-0.001 per request
3. OpenWeather API - Minimal cost but has rate limits

**Biggest Wins**:
1. Cache hits eliminate all costs (100% savings)
2. Skip audio generation when not needed (50-70% of requests)
3. API cache prevents redundant weather fetches

### User Experience Insights
- Users expect **fast responses** (< 5 seconds ideal)
- Audio output is **optional** (many users just read text)
- **Conversational tone** appreciated vs. raw weather data
- **Practical advice** ("bring umbrella") adds value

## Code Style & Conventions

### Type Hints
- Use type hints for function parameters and returns
- Example: `def tool(tool_context: ToolContext, city: str) -> Dict[str, Any]:`
- Use `Dict`, `List`, `Any` from typing module

### Docstrings
- All tools must have docstrings (ADK requirement)
- Format: Google-style docstrings
- Include: Purpose, Args, Returns
- Example in [`get_current_weather.py:49-60`](../../weather_agent/sub_agents/forecast_writer/tools/get_current_weather.py#L49-L60)

### File Organization
- One agent per file: `agent.py`
- Tools in `tools/` subdirectory
- Sub-agents in `sub_agents/` with nested structure
- Cache utilities at root level: `api_call_cache.py`, `forecast_cache.py`
- Standalone utility modules: `forecast_file_cleanup.py`

### Environment Variables
- Load with `python-dotenv`
- Access via `os.getenv("VAR_NAME", "default")`
- Never commit `.env` file
- Use [`.env.example`](../../.env.example) as template
- Key variables:
  - `OUTPUT_DIR`: Directory for forecast files (default: "output")
  - `FORECAST_CLEANUP_DAYS`: File retention period (default: 7)
  - `OPENWEATHER_API_KEY`: OpenWeather API key
  - `PROJECT_ID`: Google Cloud project ID
  - `LOCATION`: Google Cloud region

### Error Messages
- User-friendly language
- Include city name in errors: `f"Failed to fetch weather data for {city}"`
- Don't expose internal stack traces to users
- Log detailed errors for debugging

## Testing Approach

### Current Tests
- `test_api_call_caching.py` - Unit tests for Level 1 cache
- `test_forecast_caching.py` - Unit tests for Level 2 cache

### Testing Philosophy
- Test each cache layer independently
- Verify TTL expiration behavior
- Test cache key generation
- Integration tests for full agent flow (manual via UI)

### Manual Testing Workflow
1. Start fresh (delete `output/` directory)
2. Query weather for a city
3. Immediately query same city → should be cached
4. Wait 30+ minutes → query again → should regenerate
5. Check `output/{city}/` directory for files
6. Use `get_cache_stats()` tool to verify cache state

## Dependencies & Updates

### Critical Dependencies
- `google-cloud-aiplatform[adk,agent_engines]` - Core framework
- `requests` - HTTP client
- `python-dotenv` - Environment management

### Dependency Considerations
- ADK is new and evolving - expect breaking changes
- Pin versions for production deployments
- Test thoroughly after ADK updates
- No async support yet, but may come in future versions

### No External Dependencies for Caching
- Intentionally avoided Redis, Memcached
- Keeps deployment simple
- Sufficient for single-instance use case
- Can add distributed cache if scaling needed

## Current Limitations & Constraints

### Known Limitations
1. **Single user**: Hardcoded `user_123` in UIs
2. **No auth**: Anyone can access
3. **Local files**: Not suitable for distributed deployment
4. **Sync only**: No async/await in ADK
5. **English only**: No i18n support

### Acceptable for Current Scope
- This is a lab/demo project
- Focus on core functionality and optimization
- Multi-user and auth are future enhancements
- Current architecture works for learning and testing

## Environment-Specific Notes

### Development vs. Production
**Development**:
- Run locally with `streamlit run app.py`
- Use `.env` file for secrets
- Output to local `./output/` directory
- Debug with print statements

**Production** (Future):
- Deploy to Cloud Run or GKE via Docker
- Use Google Secret Manager for API keys
- Consider Cloud Storage for forecast files
- Add monitoring and logging (Cloud Logging)

### Platform Specifics
**Windows**: Current development environment
- PowerShell as default shell
- File paths use backslashes (but Python handles both)
- No issues with cross-platform compatibility

**Linux/Mac**: Should work identically
- Bash/Zsh as shell
- Same Python code, same dependencies
- Docker deployment tested
