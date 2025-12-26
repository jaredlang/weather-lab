# Product Context: Weather Lab

## Why This Project Exists

### Problem Statement
Users need quick, accurate, and engaging weather information delivered in a conversational manner. Traditional weather apps are static and impersonal. This project creates an AI-powered weather assistant that:
- Provides current weather data on demand
- Generates natural, conversational forecasts
- Offers audio output for hands-free consumption
- Reduces response times through intelligent caching

### Target Users
- People seeking quick weather updates
- Users who prefer conversational interfaces over traditional apps
- Developers learning about multi-agent AI systems
- Anyone interested in voice-enabled weather information

## How It Should Work

### User Flow
1. **User Initiates**: User asks about weather in a specific city via chat interface
2. **City Detection**: Root agent extracts city name and weather type from user query
3. **Cache Check**: System checks if recent forecast exists (< 30 minutes old)
4. **If Cached**:
   - Retrieve stored text and audio files
   - Return immediately (1-2 second response)
5. **If Not Cached**:
   - Delegate to forecast_writer_agent → Fetch weather data → Generate text forecast
   - Conditionally delegate to forecast_speaker_agent → Generate audio (if requested)
   - Cache results for future requests
   - Return to user (5-15 second response)

### Key Features

#### 1. Multi-Agent System
- **Root Agent**: Orchestrates workflow, manages caching, routes requests
- **Forecast Writer Agent**: Fetches weather data, generates conversational text
- **Forecast Speaker Agent**: Converts text to natural-sounding audio

#### 2. Intelligent Caching
- **Weather API Cache**: 15-minute TTL for raw weather data
- **Complete Forecast Cache**: 30-minute TTL for text + audio pairs
- **Filesystem-Based**: Files are source of truth, survives restarts

#### 3. Cost Optimization
- Cache hits avoid redundant API calls
- Conditional audio generation (only when user needs it)
- Session state prevents duplicate LLM calls

#### 4. User Experience Goals
- **Fast**: < 2 seconds for cached, < 15 seconds for fresh
- **Conversational**: Natural language, friendly tone
- **Practical**: Includes advice ("bring umbrella", "dress warmly")
- **Multi-Modal**: Both text and audio output available
- **Reliable**: Graceful error handling, never crashes

## What Makes This Special

### Technical Innovation
- **Two-Level Caching**: API-level (15 min) + forecast-level (30 min)
- **Filesystem as Truth**: No in-memory state complexity
- **Conditional Execution**: Skip expensive audio generation when not needed
- **Google ADK Integration**: Leverages cutting-edge agent framework

### User Benefits
- Lightning-fast cached responses
- Engaging, personality-filled forecasts
- Voice output for hands-free use
- Always up-to-date weather information

## Current State
The system is functionally complete with:
- ✅ Full multi-agent architecture
- ✅ Two-level caching implementation
- ✅ Streamlit and Chainlit UIs
- ✅ Weather API integration (OpenWeather)
- ✅ TTS audio generation (Google Gemini)
- ✅ File-based persistence
- ✅ Session state management

## Future Enhancements
See [`improvement-plan.md`](../../weather_agent/improvement-plan.md) for detailed optimization roadmap covering:
- Retry logic with exponential backoff
- Request timeouts
- Connection pooling
- Rate limiting protection
- Monitoring and metrics
- Async/await refactoring (if ADK supports it)
