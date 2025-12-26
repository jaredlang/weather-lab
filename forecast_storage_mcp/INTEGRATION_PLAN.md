# Weather Agent Integration Plan

## Overview

Replace filesystem-based caching with Cloud SQL MCP server for forecast storage.

## Current Architecture

```
Weather Agent
├── forecast_cache.py (filesystem scan)
│   ├── get_forecast_from_cache() → scans OUTPUT_DIR
│   ├── cache_forecast() → no-op (files already written)
│   └── get_cache_stats() → scans directories
│
├── generate_audio.py
│   └── Saves audio to local OUTPUT_DIR/{city}/
│
└── forecast_writer (implicit)
    └── Saves text to session state
```

## New Architecture

```
Weather Agent
├── forecast_storage_client.py (NEW - MCP client wrapper)
│   ├── upload_forecast_to_storage() → calls MCP upload_forecast
│   ├── get_cached_forecast_from_storage() → calls MCP get_cached_forecast
│   └── get_storage_stats_from_mcp() → calls MCP get_storage_stats
│
├── generate_audio.py (MODIFIED)
│   └── Saves audio temporarily, returns path for upload
│
└── agent.py (MODIFIED)
    └── Uses MCP client wrapper tools instead of forecast_cache
```

## Changes Required

### 1. Create MCP Client Wrapper
**File**: `weather_agent/forecast_storage_client.py`

Wrapper functions that call MCP server tools:
- `upload_forecast_to_storage(city, text, audio_path, timestamp)`
- `get_cached_forecast_from_storage(city)`
- `get_storage_stats_from_mcp()`

### 2. Modify generate_audio.py
**File**: `weather_agent/sub_agents/forecast_speaker/tools/generate_audio.py`

**Current behavior**: Saves directly to `OUTPUT_DIR/{city}/forecast_audio_{timestamp}.wav`

**New behavior**: 
- Save to temporary location
- Return path for agent to upload via MCP
- Agent handles upload after both text and audio are ready

### 3. Update agent.py
**File**: `weather_agent/agent.py`

**Replace**:
```python
from .forecast_cache import get_forecast_from_cache, cache_forecast, get_cache_stats
```

**With**:
```python
from .forecast_storage_client import (
    get_cached_forecast_from_storage, 
    upload_forecast_to_storage,
    get_storage_stats_from_mcp
)
```

**Update instructions**:
- Use `get_cached_forecast_from_storage` instead of `get_forecast_from_cache`
- Use `upload_forecast_to_storage` after sub-agents complete
- Handle MCP response format (JSON with status)

### 4. Configuration
**File**: `.env` (project root)

Add MCP server endpoint:
```bash
# Option A: MCP Server runs as subprocess
MCP_FORECAST_STORAGE_PATH=./forecast_storage_mcp/server.py

# Option B: MCP Server runs externally
MCP_FORECAST_STORAGE_URL=http://localhost:3000
```

## Migration Steps

1. ✅ Create MCP server (DONE)
2. ⏳ Create MCP client wrapper
3. ⏳ Modify generate_audio.py
4. ⏳ Update agent.py instructions and tools
5. ⏳ Test with sample forecast
6. ⏳ Deprecate forecast_cache.py (keep for reference)

## Backward Compatibility

During transition:
- Keep both systems (filesystem + Cloud SQL)
- Add flag: `USE_CLOUD_SQL_STORAGE=true/false`
- Gradual migration path

## Testing Strategy

1. **Unit tests**: Test MCP client wrapper functions
2. **Integration test**: 
   - Generate forecast → Upload to Cloud SQL
   - Request same city → Retrieve from cache
   - Verify TTL expiration
3. **End-to-end test**: Full agent workflow with MCP storage

## Rollback Plan

If issues arise:
1. Set `USE_CLOUD_SQL_STORAGE=false`
2. Agent falls back to filesystem cache
3. Debug MCP integration separately
