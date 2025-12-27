# Active Context: Weather Lab

## Current State
Memory bank initialized on 2025-12-27. The weather lab project has been built with three main components working together to provide weather forecasts with caching and multiple access interfaces.

## Recent Changes
- Memory bank structure created with all core files
- Project documented with architecture, patterns, and technical details

## Current Work Focus
Memory bank initialization complete. System is ready for development work.

## Next Steps

### Immediate Priorities
1. **Verify system functionality** - Ensure all three components can run:
   - Weather agent with MCP client
   - Forecast storage MCP server
   - Forecast REST API

2. **Test integrations** - Validate end-to-end flows:
   - Agent → MCP server → Cloud SQL
   - REST API → Cloud SQL direct
   - Caching at all levels working

3. **Optimization validation** - Confirm implemented optimizations:
   - API call caching (15 min TTL)
   - Forecast caching (30 min TTL) in Cloud SQL
   - File cleanup working
   - Conditional audio generation

### Future Enhancements
- Monitor cache hit rates in production
- Add more comprehensive metrics collection
- Implement additional language support testing
- Load testing for production readiness

## Active Decisions

### Architecture Decisions
1. **MCP over stdio:** Using remote MCP (SSE) instead of stdio for Cloud Run compatibility
2. **Direct SQL for REST API:** Bypassing MCP for API clients to reduce latency
3. **Binary storage:** Using BYTEA in PostgreSQL for unicode support across all languages
4. **Base64 audio:** Encoding audio in base64 for remote MCP server compatibility

### Performance Trade-offs
1. **15-min API cache:** Balance between freshness and cost savings
2. **30-min forecast cache:** Longer TTL for expensive LLM+TTS operations
3. **Conditional audio:** Only generate when explicitly requested (saves 50-70% TTS costs)
4. **7-day file retention:** Balance between disk space and debugging needs

### Technology Choices
1. **FastAPI over Flask:** Better async support and auto-generated docs
2. **PostgreSQL over MySQL:** Better JSONB support for flexible metadata
3. **Cloud SQL Connector:** More secure than public IP connections
4. **pytest over unittest:** More Pythonic and better fixtures

## Important Patterns

### 1. Cache-First Pattern
Always check Cloud SQL cache before generating new forecasts. This is the #1 cost and performance optimization.

**Implementation:**
```python
# Check cache first (in root agent instruction)
result = await get_cached_forecast_from_storage(city=city)
if result.get("cached"):
    # Skip sub-agents entirely, use cached data
    return cached_forecast
else:
    # Generate new forecast via sub-agents
    delegate_to_weather_studio_team()
```

### 2. Conditional Execution Pattern
Only run expensive operations when needed (audio generation, uploads).

**Implementation:**
```python
# Conditional upload callback
async def conditional_upload_forecast(callback_context):
    if callback_context.state.get("FORECAST_CACHED", False):
        return  # Skip upload if already cached
    await upload_forecast_to_storage(callback_context)
```

### 3. Fire-and-Forget Cleanup
Don't block responses waiting for file cleanup.

**Implementation:**
```python
# Background cleanup (no await)
asyncio.create_task(cleanup_old_forecast_files_async())
```

### 4. Session State Sharing
Use shared state dictionary for agent coordination.

**Key State Variables:**
- `CITY` - User's requested city
- `FORECAST_TEXT` - Generated forecast text
- `FORECAST_AUDIO` - Audio file path
- `FORECAST_CACHED` - Whether from cache (skip upload)
- `FORECAST_TIMESTAMP` - When forecast was generated

### 5. Retry with Backoff
Handle transient failures gracefully.

**Pattern:**
- Retry transient errors (5xx, timeouts)
- Don't retry client errors (4xx, validation)
- Exponential backoff: 1s → 2s → 4s
- Max 3 retries

## Learnings & Insights

### What Works Well
1. **Multi-level caching** dramatically reduces costs (80%+ savings)
2. **MCP protocol** provides clean agent-to-storage abstraction
3. **Cloud SQL** handles concurrent requests and TTL expiration well
4. **Binary storage** supports all languages without encoding issues
5. **FastAPI** auto-docs are valuable for API consumers

### Challenges Overcome
1. **Remote MCP base64 audio:** MCP server can't access local files, so encode audio as base64
2. **Sequential agent overhead:** Conditional execution prevents unnecessary audio generation
3. **Unicode storage:** BYTEA with encoding metadata supports all languages
4. **Connection pooling:** Reusing connections reduces latency significantly
5. **Windows compatibility:** Use PowerShell scripts instead of bash

### Known Limitations
1. **No async agents:** Google ADK may not support fully async agent execution
2. **Single region:** Currently only US-Central1 for Cloud SQL
3. **No auth:** APIs are unauthenticated (suitable for internal use only)
4. **Manual scaling:** No auto-scaling metrics for Cloud Run instances yet
5. **Limited monitoring:** Metrics collection exists but not exported to dashboard

## Debugging Tips

### Common Issues

**1. MCP Connection Failures**
```
Error: Cannot connect to MCP server at http://localhost:8080
```
**Solution:** Ensure MCP server is running: `python forecast_storage_mcp/server.py`

**2. Cloud SQL Connection Errors**
```
Error: Failed to connect to Cloud SQL instance
```
**Solution:** 
- Verify `.env` has correct credentials
- Check Cloud SQL instance is running
- Verify Cloud SQL Connector has access

**3. Cache Not Working**
```
Cache hit rate: 0%
```
**Solution:**
- Check TTL values (15 min API, 30 min forecast)
- Verify Cloud SQL connection
- Check `expires_at` timestamp in database

**4. Audio Generation Failures**
```
Error: Google TTS API failed
```
**Solution:**
- Verify Google Cloud credentials
- Check TTS API is enabled in GCP project
- Verify language/locale are supported

### Debugging Commands

**Check MCP server health:**
```python
python -c "from forecast_storage_mcp.tools.connection import test_connection; import json; print(json.dumps(test_connection(), indent=2))"
```

**Check API health:**
```powershell
curl http://localhost:8000/health
```

**Query database directly:**
```sql
SELECT city, language, forecast_at, expires_at 
FROM forecasts 
WHERE expires_at > NOW() 
ORDER BY created_at DESC 
LIMIT 10;
```

**Check cache statistics:**
```powershell
curl http://localhost:8000/stats
```

## Environment-Specific Notes

### Windows 11 Considerations
- Use PowerShell 7, not Command Prompt
- Use `.\script.bat` or `.\script.ps1` for scripts
- Path separators: Use forward slashes in Python (cross-platform)
- Line endings: Git should handle CRLF ↔ LF automatically

### Local Development Setup
1. Install Python 3.11+
2. Create virtual environment: `python -m venv venv`
3. Activate: `.\venv\Scripts\Activate.ps1`
4. Install dependencies in each component
5. Configure `.env` files
6. Start MCP server first, then agent/API

### Cloud Deployment Setup
1. Create Cloud SQL instance
2. Apply schema: `schema.sql`
3. Build Docker images
4. Push to Artifact Registry
5. Deploy to Cloud Run
6. Update `MCP_SERVER_URL` in agent `.env`

## Project Insights

### Why This Architecture?
1. **Separation of concerns:** Agent logic separate from storage and API
2. **Multiple interfaces:** Same data accessible via agents and REST
3. **Cloud-native:** Designed for Cloud Run deployment from day one
4. **Cost-optimized:** Aggressive caching at multiple levels
5. **Language-agnostic:** Binary storage supports any unicode text

### Design Philosophy
1. **Cache everything:** Weather doesn't change minute-to-minute
2. **Generate conditionally:** Only create what's needed (audio)
3. **Fail gracefully:** Return cached data or clear errors
4. **Be observable:** Log for debugging, metrics for optimization
5. **Stay simple:** Minimal dependencies, clear patterns

### Success Metrics Tracked
- Cache hit rate (target: > 80%)
- Response time (cached: < 1s, new: < 10s)
- API call reduction (target: > 80%)
- Cost per forecast (target: < $0.01)
- Uptime (target: > 99.9%)

## References

### Key Files to Know
- [`weather_agent/agent.py`](weather_agent/agent.py) - Root agent orchestration
- [`weather_agent/forecast_storage_client.py`](weather_agent/forecast_storage_client.py) - MCP client wrapper
- [`forecast_storage_mcp/server.py`](forecast_storage_mcp/server.py) - MCP SSE server
- [`forecast_api/main.py`](forecast_api/main.py) - REST API entry point
- [`weather_agent/improvement-plan.md`](weather_agent/improvement-plan.md) - Optimization roadmap

### Documentation Files
- [`forecast_storage_mcp/README.md`](forecast_storage_mcp/README.md) - MCP server setup
- [`forecast_api/README.md`](forecast_api/README.md) - REST API guide
- [`forecast_api/TESTING.md`](forecast_api/TESTING.md) - Testing guide
- [`forecast_storage_mcp/DEPLOYMENT.md`](forecast_storage_mcp/DEPLOYMENT.md) - Deployment guide

### Schema & Config
- [`forecast_storage_mcp/schema.sql`](forecast_storage_mcp/schema.sql) - Database schema
- `.env.example` files - Environment templates in each component

## Communication Patterns

### Agent → MCP Server
- Protocol: MCP over SSE
- Authentication: None (internal network)
- Data format: JSON
- Audio: Base64-encoded

### REST API → Cloud SQL
- Protocol: Direct SQL via Cloud SQL Connector
- Authentication: Database password
- Data format: PostgreSQL wire protocol
- Audio: Base64 in JSON response

### External APIs
- OpenWeather: REST with API key
- Gemini: Google ADK handles auth
- Google TTS: Google Cloud SDK handles auth
