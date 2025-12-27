# MCP Server Cloud Run Deployment Guide

This guide explains how to deploy the Forecast Storage MCP server to Google Cloud Run.

## Prerequisites

1. Google Cloud Project with billing enabled
2. Cloud SQL PostgreSQL instance set up (see main README for schema setup)
3. gcloud CLI installed and authenticated
4. Docker installed locally (optional, Cloud Build can handle this)

## Environment Setup

### 1. Set Project Variables

```bash
# Set your project configuration
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export SERVICE_NAME="forecast-mcp-server"
export INSTANCE_CONNECTION_NAME="your-project-id:your-region:your-instance-name"
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

### 3. Create Database Secret

Store your database password in Secret Manager:

```bash
# Create secret for database password
echo -n "your-database-password" | \
  gcloud secrets create forecast-db-password \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Grant Cloud Run service account access to secret
gcloud secrets add-iam-policy-binding forecast-db-password \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

## Build and Deploy

### Option 1: Build with Cloud Build and Deploy

```bash
# Navigate to MCP server directory
cd forecast_storage_mcp

# Build and deploy in one command
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
  --set-env-vars "MCP_TRANSPORT=http,DB_NAME=forecasts,DB_USER=postgres,INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME" \
  --set-secrets "DB_PASSWORD=forecast-db-password:latest" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --max-instances 10 \
  --min-instances 0 \
  --project $PROJECT_ID
```

### Option 2: Build Locally and Deploy

```bash
# Navigate to MCP server directory
cd forecast_storage_mcp

# Build container image
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --project $PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
  --set-env-vars "MCP_TRANSPORT=http,DB_NAME=forecasts,DB_USER=postgres,INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME" \
  --set-secrets "DB_PASSWORD=forecast-db-password:latest" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --max-instances 10 \
  --min-instances 0 \
  --project $PROJECT_ID
```

## Get Service URL

After deployment, get the service URL:

```bash
gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)' \
  --project $PROJECT_ID
```

Example output: `https://forecast-mcp-server-xxxxx-uc.a.run.app`

## Configure Weather Agent

Update the weather agent's `.env` file to use the remote MCP server:

```bash
# In weather_agent/.env
MCP_SERVER_URL=https://forecast-mcp-server-xxxxx-uc.a.run.app
```

## Testing the Deployment

### Test Health Check

```bash
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)' \
  --project $PROJECT_ID)

# Test connection tool
curl -X POST "${SERVICE_URL}/messages" \
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

### Test MCP Tool Call

```bash
# Test get_cached_forecast
curl -X POST "${SERVICE_URL}/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_cached_forecast",
      "arguments": {
        "city": "chicago"
      }
    }
  }'
```

## Update Existing Deployment

To update the service with new code:

```bash
cd forecast_storage_mcp

# Rebuild and redeploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID
```

## Monitoring and Logs

### View Logs

```bash
# Stream logs
gcloud run services logs tail $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID

# View recent logs
gcloud run services logs read $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --limit 50 \
  --project $PROJECT_ID
```

### View Metrics

```bash
# Open Cloud Run service in Cloud Console
gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID
```

Visit the Cloud Console URL to view:
- Request count and latency
- Container instance count
- Memory and CPU usage
- Error rates

## Cost Optimization

### Set Minimum Instances

For production with consistent traffic:

```bash
gcloud run services update $SERVICE_NAME \
  --min-instances 1 \
  --region $REGION \
  --project $PROJECT_ID
```

### Enable CPU Throttling

Reduce costs during idle periods:

```bash
gcloud run services update $SERVICE_NAME \
  --cpu-throttling \
  --region $REGION \
  --project $PROJECT_ID
```

## Security Considerations

### Enable Authentication (Optional)

To require authentication:

```bash
# Update to require authentication
gcloud run services update $SERVICE_NAME \
  --no-allow-unauthenticated \
  --region $REGION \
  --project $PROJECT_ID

# Grant weather agent service account access
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --member="serviceAccount:weather-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region $REGION \
  --project $PROJECT_ID
```

### Use VPC Connector (Advanced)

For private network access:

```bash
# Create VPC connector (one-time setup)
gcloud compute networks vpc-access connectors create forecast-connector \
  --region $REGION \
  --range 10.8.0.0/28 \
  --project $PROJECT_ID

# Update service to use connector
gcloud run services update $SERVICE_NAME \
  --vpc-connector forecast-connector \
  --region $REGION \
  --project $PROJECT_ID
```

## Troubleshooting

### Check Service Status

```bash
gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID
```

### Common Issues

1. **Cloud SQL Connection Failed**
   - Verify `INSTANCE_CONNECTION_NAME` is correct
   - Check service account has Cloud SQL Client role
   - Ensure Cloud SQL instance is running

2. **Secret Access Denied**
   - Verify secret exists: `gcloud secrets describe forecast-db-password`
   - Check IAM permissions on secret

3. **Container Fails to Start**
   - Check logs: `gcloud run services logs read $SERVICE_NAME`
   - Verify environment variables are set correctly
   - Test container locally with Docker

### Local Testing with Docker

```bash
cd forecast_storage_mcp

# Build image
docker build -t forecast-mcp-server .

# Run locally (stdio mode for testing)
docker run -it \
  -e MCP_TRANSPORT=stdio \
  -e DB_NAME=forecasts \
  -e DB_USER=postgres \
  -e DB_PASSWORD=your-password \
  forecast-mcp-server
```

## Rolling Back

If deployment fails:

```bash
# List revisions
gcloud run revisions list \
  --service $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID

# Roll back to previous revision
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions REVISION-NAME=100 \
  --region $REGION \
  --project $PROJECT_ID
```

## Clean Up

To delete the service:

```bash
gcloud run services delete $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID
```
