# Forecast Storage MCP Server

A Model Context Protocol (MCP) server for storing weather forecasts in Google Cloud SQL PostgreSQL.

## Features

- ✅ **Binary storage** for text and audio with unicode support
- ✅ **Full internationalization** - supports all languages (English, Spanish, Chinese, Japanese, Arabic, etc.)
- ✅ **TTL-based caching** with automatic expiration
- ✅ **Cloud SQL integration** with secure connections
- ✅ **Storage statistics** and per-city breakdown
- ✅ **Automatic encoding detection** (utf-8, utf-16, utf-32)

## Setup

### 1. Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create weather-forecasts \
  --database-version=POSTGRES_17 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --enable-auto-scaling \
  --auto-scaling-min-cpu=1 \
  --auto-scaling-max-cpu=2

# Create database
gcloud sql databases create weather \
  --instance=weather-forecasts

# Set password for postgres user
gcloud sql users set-password postgres \
  --instance=weather-forecasts \
  --password=YOUR_SECURE_PASSWORD
```

### 2. Apply Database Schema

```bash
# Get the instance IP (or use Cloud SQL Proxy)
gcloud sql instances describe weather-forecasts --format="value(ipAddresses[0].ipAddress)"

# Apply schema
psql -h INSTANCE_IP -U postgres -d weather -f schema.sql
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
# GCP_PROJECT_ID=your-project-id
# CLOUD_SQL_PASSWORD=your-secure-password
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run MCP Server

```bash
python server.py
```

## MCP Tools

### 1. upload_forecast

Upload a complete forecast (text + audio) to Cloud SQL.

```json
{
  "city": "chicago",
  "forecast_text": "Weather in Chicago: Sunny, 75°F",
  "audio_data": "<base64-encoded-wav-audio-data>",
  "forecast_at": "2025-12-26T15:00:00Z",
  "ttl_minutes": 30,
  "language": "en",
  "locale": "en-US"
}
```

**Note:** `audio_data` should be base64-encoded WAV audio data, not a file path. This allows the MCP server to work in remote/containerized environments.

### 2. get_cached_forecast

Retrieve cached forecast if available and not expired.

```json
{
  "city": "chicago",
  "language": "en"
}
```

Returns:
- `cached: true/false`
- `forecast_text`: decoded unicode text
- `audio_data`: base64-encoded audio
- `age_seconds`: age of cached forecast

### 3. cleanup_expired_forecasts

Remove expired forecasts from database.

```json
{}
```

### 4. get_storage_stats

Get database storage statistics.

```json
{}
```

Returns:
- Total forecasts
- Storage sizes
- Encodings used
- Languages used
- Per-city breakdown

### 5. list_forecasts

List forecast history.

```json
{
  "city": "chicago",
  "limit": 10
}
```

### 6. test_connection

Test database connection.

```json
{}
```

## Integration with Weather Agent

The MCP server is designed to integrate with the weather agent system. See the main project README for integration details.

## Database Schema

The `forecasts` table stores:
- **Binary text** (BYTEA) with encoding metadata
- **Binary audio** (BYTEA) 
- **Unicode support** (utf-8, utf-16, utf-32)
- **Internationalization** (language, locale)
- **TTL management** (forecast_at, expires_at)
- **Storage metadata** (sizes, encoding, metadata JSONB)

## Development

### Testing Connection

```bash
# Run test connection
python -c "from tools.connection import test_connection; import json; print(json.dumps(test_connection(), indent=2))"
```

### Running Tests

```bash
# Add tests in tests/ directory
pytest tests/
```

## Troubleshooting

### Connection Issues

1. Verify Cloud SQL instance is running
2. Check firewall rules allow connections
3. Verify credentials in .env file
4. Test with `test_connection` tool

### Encoding Issues

- Default encoding is utf-8 (works for most languages)
- Use utf-16 for heavy CJK (Chinese/Japanese/Korean) text
- Encoding is auto-detected if not specified

## Cost Estimation

**Development (db-f1-micro)**:
- Instance: ~$7/month (with auto-pause: ~$3.50/month)
- Storage (10GB): ~$1.70/month
- Total: ~$5-9/month

**Production (db-custom-2-7680)**:
- Instance: ~$130/month (with auto-pause: ~$65/month)  
- Storage (50GB): ~$8.50/month
- Total: ~$70-140/month

## License

Part of the weather-lab project.
