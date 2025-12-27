# Project Brief: Weather Lab

## Project Identity
**Name:** Weather Lab  
**Type:** Multi-agent Weather Forecasting System  
**Primary Language:** Python  
**Architecture:** Distributed (Agent System + MCP Server + REST API)

## Core Purpose
Build a production-grade weather forecasting system that retrieves weather data, generates natural language forecasts, converts them to speech, and stores/serves them efficiently through multiple interfaces (agents, MCP, REST API).

## Primary Goals

### 1. Multi-Modal Weather Delivery
- Provide weather forecasts in both text and audio formats
- Support multiple languages and locales (internationalization)
- Cache forecasts to reduce costs and improve response times

### 2. Scalable Storage Architecture
- Store forecasts in Cloud SQL PostgreSQL with TTL-based expiration
- Support binary storage for text (unicode) and audio data
- Provide MCP server for agent integration
- Offer REST API for external consumers

### 3. Cost & Performance Optimization
- Reduce operational costs by 80-95% through intelligent caching
- Improve response speed by 60-90% through optimization
- Achieve near 100% reliability through retry logic and error handling

### 4. Production-Ready Quality
- Comprehensive test coverage for all components
- Monitoring and metrics collection
- Docker containerization for deployment
- Cloud Run deployment support

## Key Requirements

### Functional Requirements
1. **Weather Data Retrieval**
   - Fetch current weather from OpenWeather API
   - Support multiple cities globally
   - Handle API rate limits and failures gracefully

2. **Forecast Generation**
   - Use LLM (Gemini) to generate conversational forecasts
   - 3-4 sentence friendly announcements
   - Include practical advice (umbrella, dress warmly, etc.)

3. **Audio Generation**
   - Convert text forecasts to speech using Google TTS
   - Generate WAV audio files
   - Store audio as base64 in database and API responses

4. **Caching Strategy**
   - Multi-level caching: API calls (15 min), forecasts (30 min)
   - Cloud SQL as central cache with TTL expiration
   - File cleanup for old local forecasts

5. **Storage & Retrieval**
   - MCP server for agent-to-storage communication
   - REST API for external client access
   - Support for forecast history and statistics

### Non-Functional Requirements
1. **Performance**
   - Response time < 3 seconds for cached forecasts
   - Response time < 10 seconds for new forecasts
   - Handle 60+ requests per minute

2. **Reliability**
   - 99.9% uptime target
   - Automatic retry on transient failures
   - Graceful degradation on service unavailability

3. **Cost Efficiency**
   - Minimize OpenWeather API calls (60/min free tier)
   - Reduce LLM token usage through caching
   - Optimize TTS usage (conditional generation)

4. **Maintainability**
   - Clear separation of concerns (agents, storage, API)
   - Comprehensive testing and documentation
   - Monitoring and metrics for observability

## Success Criteria
- ✅ Weather forecasts delivered in text and audio formats
- ✅ Multi-language support working (en, es, ja, zh, etc.)
- ✅ Caching reduces API calls by 80%+
- ✅ Response times improved by 60%+
- ✅ Test coverage > 80%
- ✅ Cloud deployment operational
- ✅ Production costs < $20/month

## Out of Scope
- Historical weather analysis or trends
- Weather alerts or notifications
- Mobile/web UI (API-only for now)
- Real-time weather updates (polling-based is sufficient)
- Multi-user authentication/authorization

## Constraints
- Must use free tier of OpenWeather API (60 calls/min)
- Must work on Windows 11 (PowerShell, not Bash)
- Must support Google Cloud Platform deployment
- Python 3.11+ required
- Google ADK for agent framework
