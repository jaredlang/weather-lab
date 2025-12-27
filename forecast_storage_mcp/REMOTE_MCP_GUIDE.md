# Remote MCP Server Guide

This guide explains how the weather agent works with the MCP server via HTTP/SSE transport.

## Quick Start

**TL;DR - What took 3-4 hours to figure out:**

1. **MCP server must use SSE (Server-Sent Events) transport, not HTTP POST**
2. **Client must connect via `/sse` endpoint, not `/messages`**
3. **Audio data must be base64-encoded, not file paths**
4. **MCP client library handles the JSON-RPC protocol automatically**

See [Implementation Summary](#implementation-summary) for detailed changes.

## Architecture Overview

```text
Weather Agent → SSE/JSON-RPC → MCP Server (SSE/HTTP) → Cloud SQL
```

The weather agent **always** calls the MCP server remotely via SSE transport using the MCP protocol. This works for both:
- **Local Development**: MCP server running on `localhost:8080`
- **Production**: MCP server deployed on Cloud Run

## How It Works

### MCP Server (`forecast_storage_mcp/server.py`)

The MCP server runs in HTTP mode and exposes endpoints:
- `/sse` - Server-Sent Events endpoint for streaming
- `/messages` - POST endpoint for tool calls

Transport mode is controlled by the `MCP_TRANSPORT` environment variable:
- `MCP_TRANSPORT=http` - HTTP mode (required)

### Client (`weather_agent/forecast_storage_client.py`)

The client makes HTTP POST requests to the MCP server using JSON-RPC 2.0:
- Sends tool name and arguments
- Receives results as JSON
- Handles timeouts and connection errors

The MCP server URL is configured via `MCP_SERVER_URL` environment variable.

## Configuration

### For Local Development

1. Start MCP server on localhost:
```bash
cd forecast_storage_mcp
MCP_TRANSPORT=http PORT=8080 python server.py
```

2. Configure weather agent to use localhost:
```bash
# weather_agent/.env
MCP_SERVER_URL=http://localhost:8080
```

### For Production (Cloud Run)

1. Deploy MCP server to Cloud Run (see [DEPLOYMENT.md](./DEPLOYMENT.md))

2. Configure weather agent with Cloud Run URL:
```bash
# weather_agent/.env
MCP_SERVER_URL=https://forecast-mcp-server-xxxxx-uc.a.run.app
```

## Testing

### Test Local HTTP Server

```bash
# Terminal 1: Start MCP server
cd forecast_storage_mcp
MCP_TRANSPORT=http PORT=8080 python server.py

# Terminal 2: Test with weather agent
cd ..
python test_remote_mcp.py local
```

### Test Cloud Run Deployment

```bash
export MCP_SERVER_URL=https://forecast-mcp-server-xxxxx-uc.a.run.app
python test_remote_mcp.py remote
```

### Test with curl

```bash
# Local
curl -X POST "http://localhost:8080/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "test_connection",
      "arguments": {}
    }
  }'

# Cloud Run
curl -X POST "https://your-service.run.app/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "test_connection",
      "arguments": {}
    }
  }'
```

## MCP Protocol Details

### JSON-RPC 2.0 Request Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  }
}
```

### JSON-RPC 2.0 Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"status\": \"success\", \"data\": \"...\"}"
      }
    ]
  }
}
```

## Available Tools

All tools are accessed via HTTP:

1. **upload_forecast** - Store forecast text and audio in Cloud SQL
2. **get_cached_forecast** - Retrieve cached forecast if available
3. **get_storage_stats** - Get database statistics
4. **cleanup_expired_forecasts** - Remove expired forecasts
5. **list_forecasts** - List forecast history
6. **test_connection** - Verify database connectivity

## Development Workflow

### 1. Start MCP Server Locally

```bash
cd forecast_storage_mcp
MCP_TRANSPORT=http PORT=8080 python server.py
```

Keep this running in a dedicated terminal.

### 2. Develop Weather Agent

```bash
# Ensure MCP_SERVER_URL points to localhost
export MCP_SERVER_URL=http://localhost:8080

# Run your weather agent
cd weather_agent
python agent.py
```

### 3. Deploy to Production

```bash
# Deploy MCP server
cd forecast_storage_mcp
gcloud run deploy forecast-mcp-server --source . --region us-central1

# Get service URL
SERVICE_URL=$(gcloud run services describe forecast-mcp-server \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

# Update weather agent configuration
echo "MCP_SERVER_URL=$SERVICE_URL" >> ../weather_agent/.env

# Deploy weather agent to your platform
```

## Performance Considerations

### Local Development
- **Latency**: ~10-50ms (localhost HTTP)
- **Cold Start**: None (server always running)
- **Best for**: Development, testing, debugging

### Cloud Run Production
- **Latency**: ~100-500ms (network + cold start)
- **Cold Start**: ~2-5s for first request after idle
- **Scaling**: Automatic based on traffic
- **Best for**: Production deployments

### Optimization Tips

1. **Reduce Cold Starts**: Set `--min-instances 1` in Cloud Run
2. **Increase Timeout**: Use 30-60s timeout for complex operations
3. **Monitor Performance**: Use Cloud Run metrics to track latency
4. **Connection Pooling**: MCP server reuses database connections

## Troubleshooting

### Cannot Connect to MCP Server

**Error**: `Cannot connect to MCP server at http://localhost:8080`

**Solutions**:
1. Check if MCP server is running:
   ```bash
   curl http://localhost:8080/messages
   ```

2. Start MCP server:
   ```bash
   cd forecast_storage_mcp
   MCP_TRANSPORT=http PORT=8080 python server.py
   ```

3. Check port availability:
   ```bash
   netstat -an | grep 8080
   ```

### MCP Server Request Timed Out

**Error**: `MCP server request timed out`

**Solutions**:
1. Check MCP server logs for errors
2. Verify database connectivity
3. Increase timeout in client code (default: 30s)
4. For Cloud Run, check if service is scaled to zero

### Database Connection Failed

**Error**: `Connection to Cloud SQL failed`

**Solutions**:
1. Verify Cloud SQL instance is running
2. Check database credentials in `.env`
3. Test connection:
   ```bash
   cd forecast_storage_mcp
   python -c "from tools.connection import test_connection; print(test_connection())"
   ```

### Invalid MCP Response Format

**Error**: `Invalid MCP response format`

**Solutions**:
1. Check MCP server version compatibility
2. Verify JSON-RPC 2.0 response structure
3. Check server logs for errors
4. Ensure server is running in HTTP mode (not stdio)

## Best Practices

### For Development
- Run MCP server in dedicated terminal
- Use localhost URL for fastest iteration
- Monitor server logs for errors
- Test with `test_remote_mcp.py` script

### For Production
- Deploy MCP server to Cloud Run
- Enable Cloud Run authentication
- Set appropriate timeout values
- Monitor Cloud Run metrics
- Configure min instances for low latency
- Use Cloud SQL connection pooling

### For Security
- Use HTTPS for production (Cloud Run provides this)
- Enable authentication on Cloud Run endpoints
- Rotate database credentials regularly
- Use Secret Manager for sensitive values
- Limit Cloud Run service account permissions

## Migration from Direct Imports

If you previously used direct imports:

1. **Start MCP Server**: Run in HTTP mode on localhost
2. **Update Configuration**: Set `MCP_SERVER_URL=http://localhost:8080`
3. **Test**: Run `python test_remote_mcp.py local`
4. **Deploy**: MCP server to Cloud Run when ready

Benefits:
- Consistent behavior across environments
- Better separation of concerns
- Easier to scale and monitor
- Simpler deployment architecture

## Implementation Summary

This section documents the key changes made during the 3-4 hour debugging session to get remote MCP working.

### Problem 1: Transport Protocol Mismatch

**Issue**: Initially tried using HTTP POST to `/messages` endpoint with manual JSON-RPC requests.

**Root Cause**: MCP protocol uses Server-Sent Events (SSE) for bi-directional communication, not simple HTTP POST.

**Solution**:

- Changed server to use SSE transport: `MCP_TRANSPORT=http` (this enables SSE)
- Client connects via `/sse` endpoint, not `/messages`
- Use official MCP client library (`mcp.client.sse`) instead of manual HTTP requests

**Files Changed**:

- `forecast_storage_mcp/server.py`: Already configured for SSE
- `weather_agent/forecast_storage_client.py`: Updated to use `sse_client()`

### Problem 2: Audio File Path vs Base64 Data

**Issue**: Test script was passing `audio_file_path` parameter, but server expected `audio_data`.

**Root Cause**: Remote MCP server cannot access local files. Audio must be transmitted as data.

**Solution**:

- Read audio file and encode as base64 in client
- Pass `audio_data` parameter with base64 string
- Server decodes base64 back to binary

**Code Example**:

```python
# Wrong - file path won't work for remote server
result = await _call_mcp_tool_remote("upload_forecast", {
    "audio_file_path": "/path/to/file.wav"  # ❌
})

# Correct - base64 encoded data
with open(audio_path, 'rb') as f:
    audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

result = await _call_mcp_tool_remote("upload_forecast", {
    "audio_data": audio_base64  # ✅
})
```

**Files Changed**:

- `test_remote_mcp.py`: Added base64 encoding in both test functions
- `weather_agent/forecast_storage_client.py`: Already uses base64 encoding

### Problem 3: MCP Client Library Integration

**Issue**: Manual HTTP requests required complex JSON-RPC protocol handling.

**Root Cause**: Tried to bypass MCP client library, which handles protocol details.

**Solution**:

- Use `mcp.client.sse.sse_client()` for SSE connection
- Use `mcp.client.session.ClientSession` for session management
- Let library handle JSON-RPC protocol automatically

**Code Pattern**:

```python
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def _call_mcp_tool_remote(tool_name: str, arguments: Dict[str, Any]):
    base_url = MCP_SERVER_URL.rstrip('/')
    sse_url = f"{base_url}/sse"  # Connect to /sse endpoint

    async with sse_client(sse_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

            # Parse result from MCP response
            text_content = result.content[0].text
            return json.loads(text_content)
```

**Files Changed**:

- `weather_agent/forecast_storage_client.py`: Implemented SSE client pattern

### Problem 4: Test Script Default Parameter

**Issue**: Test script required command-line argument, making it harder to run.

**Solution**:

- Default to `"local"` mode when no argument provided
- Makes testing faster: just run `python test_remote_mcp.py`

**Files Changed**:

- `test_remote_mcp.py`: Updated `main()` function with default parameter

### Key Lessons Learned

1. **SSE is not optional**: MCP protocol requires SSE for proper bi-directional communication
2. **Use official client libraries**: Don't try to implement MCP protocol manually
3. **Remote servers need data, not paths**: Always encode files as base64 for remote calls
4. **Test early and often**: The `test_remote_mcp.py` script was invaluable for debugging
5. **MCP_TRANSPORT=http means SSE**: Confusing naming, but "http" enables SSE transport

### Testing Checklist

After making these changes, verify:

- [ ] MCP server starts with `MCP_TRANSPORT=http`
- [ ] Server logs show "Listening on http://localhost:8080"
- [ ] `/sse` endpoint is accessible (check server logs)
- [ ] Test script passes all 8 tests: `python test_remote_mcp.py`
- [ ] Upload forecast test succeeds (base64 encoding works)
- [ ] Weather agent can upload forecasts to storage
- [ ] Cloud Run deployment works with same code

### File Summary

**Modified Files**:

1. `weather_agent/forecast_storage_client.py` - SSE client implementation
2. `test_remote_mcp.py` - Base64 encoding + default parameter
3. `forecast_storage_mcp/server.py` - Already configured for SSE
4. `forecast_storage_mcp/REMOTE_MCP_GUIDE.md` - This documentation

**Configuration Files**:

1. `forecast_storage_mcp/.env` - Database credentials
2. `weather_agent/.env` - MCP_SERVER_URL setting

### Environment Variables

**MCP Server** (`forecast_storage_mcp/.env`):

```bash
MCP_TRANSPORT=http          # Enables SSE transport
PORT=8080                   # Server port
DB_INSTANCE=project:region:instance
DB_NAME=weather
DB_USER=postgres
DB_PASSWORD=your_password
```

**Weather Agent** (`weather_agent/.env`):

```bash
# Local development
MCP_SERVER_URL=http://localhost:8080

# Production
MCP_SERVER_URL=https://forecast-mcp-server-xxxxx-uc.a.run.app
```

### Debugging Tips

1. **Server not responding**: Check server logs for SSE connection establishment
2. **Invalid JSON errors**: Server might be returning HTML error page - check `/sse` endpoint
3. **Upload failures**: Verify base64 encoding and `audio_data` parameter name
4. **Connection timeouts**: Check firewall, Cloud Run authentication, and timeout settings

## Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Connector](https://cloud.google.com/sql/docs/postgres/connect-run)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Deployment Guide](./DEPLOYMENT.md)
