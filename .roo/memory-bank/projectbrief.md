# Project Brief: Weather Lab

## Project Overview
Weather Lab is an intelligent weather forecasting system that provides current weather information through a conversational AI interface. The system generates both text and audio weather forecasts using Google's Agent Development Kit (ADK) with multi-agent architecture.

## Core Requirements
1. **Weather Information Retrieval**: Fetch current weather data from OpenWeather API for any city
2. **Forecast Generation**: Create conversational, friendly weather forecasts (3-4 sentences)
3. **Audio Synthesis**: Convert text forecasts to natural-sounding audio using Google Gemini TTS
4. **Caching System**: Implement intelligent caching to reduce costs and improve speed
5. **Multi-Agent Architecture**: Coordinate specialized sub-agents for specific tasks
6. **User Interfaces**: Provide both Streamlit and Chainlit UIs for user interaction

## Primary Goals
- **Cost Optimization**: Reduce API calls and LLM operations through effective caching
- **Speed Improvement**: Fast response times via cache hits and optimized operations
- **Reliability**: Handle API failures gracefully with retry logic and timeouts
- **User Experience**: Friendly, conversational weather information delivery

## Key Constraints
- Must work with Google Cloud Vertex AI Agent Development Kit (ADK)
- OpenWeather API free tier limits (60 calls/minute)
- File-based output storage for forecasts (text + audio)
- Session state management for agent communication

## Success Criteria
- Weather forecasts delivered in < 5 seconds (cached) or < 15 seconds (fresh)
- 80-95% reduction in API costs through caching
- Near 100% reliability with proper error handling
- Natural, engaging text-to-speech output
- Clean, intuitive user interface

## Project Structure
```
weather-lab/
├── weather_agent/          # Core agent system
│   ├── agent.py           # Root agent orchestration
│   ├── tools.py           # Shared utilities
│   ├── api_call_cache.py  # Weather API caching
│   ├── forecast_cache.py  # Complete forecast caching
│   └── sub_agents/        # Specialized agents
├── streamlit_ui/          # Streamlit interface
├── chainlit_ui/           # Chainlit interface
└── database_mcp/          # MCP server (future)
```
