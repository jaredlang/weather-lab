# Product Context: Weather Lab

## Why This Exists

### Problem Space
Traditional weather data is raw and technical (temperatures, wind speeds, humidity). Users want:
- **Conversational forecasts** that are easy to understand
- **Practical advice** for their day (bring umbrella, dress warmly)
- **Audio delivery** for accessibility and convenience (driving, screen readers)
- **Multiple languages** for global accessibility

### User Pain Points
1. **API-first weather services** provide only raw data, not narratives
2. **Expensive TTS costs** for generating audio forecasts repeatedly
3. **Slow response times** when generating forecasts on-demand
4. **Repetitive API calls** for the same weather data within minutes
5. **No unified interface** for agent-based and REST API access

### Solution
A multi-layered weather forecasting system that:
- Fetches weather data from OpenWeather API
- Generates natural language forecasts using LLM (Gemini)
- Converts text to speech with Google TTS
- Caches everything intelligently (API data, forecasts, audio)
- Provides both agent (MCP) and REST API access
- Stores forecasts in Cloud SQL with automatic expiration

## How It Works

### User Journey (Agent Interface)

1. **User asks for weather**
   - "What's the weather in Chicago?"
   - "Do I need an umbrella in Tokyo?"

2. **Cache check (Cloud SQL)**
   - System checks if recent forecast exists (< 30 min old)
   - If cached: Return immediately (< 1 second)
   - If not cached: Proceed to generation

3. **Weather data retrieval**
   - Check API call cache (15 min TTL)
   - If cached: Use cached data
   - If not: Fetch from OpenWeather API

4. **Forecast generation**
   - LLM generates conversational 3-4 sentence forecast
   - Includes practical advice based on conditions

5. **Audio generation (conditional)**
   - Only if user requests audio output
   - Generate WAV file using Google TTS
   - Store locally and in Cloud SQL as base64

6. **Storage & delivery**
   - Upload forecast + audio to Cloud SQL
   - Return to user with text and audio file path
   - Clean up old local files in background

### User Journey (REST API)

1. **Client requests forecast**
   - `GET /weather/chicago`
   - Optional: `?language=es` for Spanish

2. **Server retrieves from Cloud SQL**
   - Direct PostgreSQL query (fast)
   - Returns latest valid forecast
   - Audio included as base64 in JSON

3. **Client receives complete package**
   - Text forecast (decoded unicode)
   - Audio data (base64-encoded WAV)
   - Metadata (timestamps, age, sizes)

## User Experience Goals

### Agent Users (Weather Agent)
**Goal:** Fast, natural weather information with optional audio

**Expectations:**
- ✅ Conversational responses, not technical data
- ✅ Practical advice for the day
- ✅ Audio output when requested
- ✅ Fast responses (< 3 seconds for cached)
- ✅ Support for any city globally
- ✅ Multi-language support

**Example Interaction:**
```
User: "What's the weather in Paris?"

Agent (cached, 30 sec):
"The weather in Paris is currently 18°C and partly cloudy. 
Perfect weather for a walk along the Seine! You might want 
to bring a light jacket for the evening. The temperature 
will drop to around 12°C after sunset."
```

### API Consumers (REST API)
**Goal:** Reliable, structured forecast data for integration

**Expectations:**
- ✅ Standard REST endpoints with JSON responses
- ✅ OpenAPI/Swagger documentation
- ✅ Audio data included in responses (base64)
- ✅ Forecast history and statistics
- ✅ Health check for monitoring
- ✅ CORS support for web apps

**Example Response:**
```json
{
  "status": "success",
  "city": "chicago",
  "forecast": {
    "text": "Weather in Chicago: Sunny, 75°F...",
    "audio_base64": "UklGRiQAAABXQVZF...",
    "forecast_at": "2025-12-27T15:00:00+00:00",
    "expires_at": "2025-12-27T15:30:00+00:00",
    "age_seconds": 120,
    "metadata": {
      "language": "en",
      "sizes": {
        "text_bytes": 1024,
        "audio_bytes": 51200
      }
    }
  }
}
```

### System Operators (Developers/DevOps)
**Goal:** Observable, maintainable, cost-effective system

**Expectations:**
- ✅ Clear logs for debugging
- ✅ Metrics for optimization (cache hit rates, latency)
- ✅ Test coverage for confidence
- ✅ Docker deployment for consistency
- ✅ Cost monitoring and alerts

## Key Features

### 1. Intelligent Caching
- **API Call Cache**: 15-minute TTL for weather data
- **Forecast Cache**: 30-minute TTL in Cloud SQL
- **File Cleanup**: Automatic removal of forecasts > 7 days old

### 2. Multi-Language Support
- **Internationalization**: Full unicode support (utf-8/16/32)
- **Language Detection**: Automatic encoding detection
- **Locale Support**: Language + region (en-US, es-MX, ja-JP)

### 3. Conditional Audio Generation
- **Smart Generation**: Only create audio when requested
- **Cost Savings**: 50-70% of requests don't need audio
- **Format**: WAV files for broad compatibility

### 4. Multiple Access Interfaces
- **MCP Server**: For agent-to-storage communication (SSE transport)
- **REST API**: For external clients (FastAPI with auto docs)
- **Direct Client**: For internal agent tools

### 5. Production-Grade Reliability
- **Retry Logic**: Exponential backoff on failures
- **Timeouts**: Prevent indefinite hangs
- **Connection Pooling**: Reuse HTTP connections
- **Rate Limiting**: Respect API quotas

## Success Metrics

### Performance Metrics
- Response time (cached): < 1 second (target)
- Response time (new): < 10 seconds (target)
- Cache hit rate: > 80% (target)
- API call reduction: > 80% (target)

### Cost Metrics
- OpenWeather API calls: < 1000/day
- LLM token usage: < 100K tokens/day
- TTS calls: < 500/day
- Cloud SQL storage: < 1 GB
- Total monthly cost: < $20

### Quality Metrics
- Uptime: > 99.9%
- Error rate: < 0.1%
- Test coverage: > 80%
- Response accuracy: 100% (correct city, current data)

## Design Principles

1. **Cache Aggressively**: Weather doesn't change minute-to-minute
2. **Generate Conditionally**: Only create what's needed
3. **Fail Gracefully**: Return cached data or clear error messages
4. **Be Observable**: Log everything important for debugging
5. **Stay Simple**: Clear separation of concerns, minimal dependencies
6. **Think Global**: Support all languages and cities from day one
