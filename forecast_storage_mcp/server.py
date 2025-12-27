"""
MCP Server for Forecast Storage

Exposes weather forecast storage operations as MCP tools.
Provides upload, retrieval, cleanup, and statistics for forecasts stored in Cloud SQL.
"""

import asyncio
import json
import os
import logging
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from tools.forecast_operations import (
    upload_forecast,
    get_cached_forecast,
    cleanup_expired_forecasts,
    get_storage_stats,
    list_forecasts
)
from tools.connection import test_connection, close_connector

# Initialize MCP server
server = Server("forecast_storage")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available forecast storage tools.
    """
    return [
        Tool(
            name="upload_forecast",
            description=(
                "Upload a complete forecast (text + audio) to Cloud SQL. "
                "Stores text as binary with unicode support and audio as binary WAV data. "
                "Automatically detects optimal text encoding and sets TTL for cache expiration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., 'chicago', 'new york')"
                    },
                    "forecast_text": {
                        "type": "string",
                        "description": "Generated forecast text content (supports all unicode languages)"
                    },
                    "audio_data": {
                        "type": "string",
                        "description": "Base64-encoded audio WAV data"
                    },
                    "forecast_at": {
                        "type": "string",
                        "description": "ISO 8601 timestamp (e.g., '2025-12-26T15:00:00Z')"
                    },
                    "ttl_minutes": {
                        "type": "integer",
                        "description": "Time-to-live in minutes (default: 30)",
                        "default": 30
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding: 'utf-8', 'utf-16', 'utf-32' (auto-detect if not specified)",
                        "enum": ["utf-8", "utf-16", "utf-32"]
                    },
                    "language": {
                        "type": "string",
                        "description": "ISO 639-1 language code (e.g., 'en', 'es', 'ja', 'zh')"
                    },
                    "locale": {
                        "type": "string",
                        "description": "Full locale (e.g., 'en-US', 'es-MX', 'ja-JP')"
                    }
                },
                "required": ["city", "forecast_text", "audio_data", "forecast_at"]
            }
        ),
        Tool(
            name="get_cached_forecast",
            description=(
                "Retrieve cached forecast from Cloud SQL if available and not expired. "
                "Returns forecast text and base64-encoded audio data if valid cache exists. "
                "Checks TTL and returns cached=False if forecast is expired."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to query"
                    },
                    "language": {
                        "type": "string",
                        "description": "Optional language filter (e.g., 'en', 'es', 'ja')"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="cleanup_expired_forecasts",
            description=(
                "Remove expired forecasts from Cloud SQL database. "
                "Deletes all forecasts where expires_at < NOW(). "
                "Returns count of deleted and remaining forecasts."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_storage_stats",
            description=(
                "Get database storage statistics including total forecasts, storage sizes, "
                "encodings used, languages used, and per-city breakdown. "
                "Useful for monitoring and capacity planning."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_forecasts",
            description=(
                "List forecast history with optional filtering by city. "
                "Returns metadata for forecasts including forecast times, sizes, encoding, and expiration status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to filter (optional, lists all if omitted)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="test_connection",
            description=(
                "Test the Cloud SQL database connection and verify setup. "
                "Returns connection status, PostgreSQL version, and table existence."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool execution requests.
    """
    # Log incoming request with structured data
    logger.info("MCP tool call request", extra={
        "tool_name": name,
        "arguments": arguments
    })

    try:
        # Route to appropriate function
        if name == "upload_forecast":
            result = upload_forecast(
                city=arguments["city"],
                forecast_text=arguments["forecast_text"],
                audio_data=arguments["audio_data"],
                forecast_at=arguments["forecast_at"],
                ttl_minutes=arguments.get("ttl_minutes", 30),
                encoding=arguments.get("encoding"),
                language=arguments.get("language"),
                locale=arguments.get("locale")
            )

        elif name == "get_cached_forecast":
            result = get_cached_forecast(
                city=arguments["city"],
                language=arguments.get("language")
            )

        elif name == "cleanup_expired_forecasts":
            result = cleanup_expired_forecasts()

        elif name == "get_storage_stats":
            result = get_storage_stats()

        elif name == "list_forecasts":
            result = list_forecasts(
                city=arguments.get("city"),
                limit=arguments.get("limit", 10)
            )

        elif name == "test_connection":
            result = test_connection()

        else:
            result = {
                "status": "error",
                "message": f"Unknown tool: {name}"
            }

        # Log response with structured data
        logger.info("MCP tool call response", extra={
            "tool_name": name,
            "result_status": result.get("status"),
            "forecast_id": result.get("forecast_id"),
            "cached": result.get("cached"),
            "result_message": result.get("message")
        })

        # Return result as JSON
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        # Log error with full stack trace
        logger.error("MCP tool call failed", extra={
            "tool_name": name,
            "error": str(e),
            "arguments": arguments
        }, exc_info=True)

        # Handle unexpected errors
        error_result = {
            "status": "error",
            "message": f"Tool execution failed: {str(e)}"
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def stdio_main():
    """
    Run MCP server in stdio mode (for local development/testing).
    """
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


async def http_main():
    """
    Run MCP server in HTTP/SSE mode (for Cloud Run deployment).
    """
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import Response
    import uvicorn

    # Create SSE transport
    logger.info("Creating SSE transport...")
    sse = SseServerTransport("/messages")
    logger.info("SSE transport created")

    async def handle_sse(request):
        """Handle SSE connection from client."""
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )
        return Response(status_code=200)
    
    async def handle_messages(request):
        """Handle incoming messages via POST."""
        # Get request body
        request_body = await request.body()

        # Log incoming request
        logger.debug("Received HTTP POST request", extra={
            "body_preview": request_body[:200].decode('utf-8', errors='replace')
        })

        async def receive():
            return {
                "type": "http.request",
                "body": request_body,
                "more_body": False,
            }

        # Response data collector
        response_data = []
        response_status = 200

        async def send(message):
            nonlocal response_status
            msg_type = message.get("type")
            logger.debug("ASGI send() called", extra={"message_type": msg_type})

            if msg_type == "http.response.start":
                response_status = message.get("status", 200)
                logger.debug("Response status set", extra={"status": response_status})
            elif msg_type == "http.response.body":
                body_chunk = message.get("body", b"")
                logger.debug("Response body chunk", extra={"chunk_length": len(body_chunk)})
                if body_chunk:
                    response_data.append(body_chunk)

        # Call SSE transport handler
        await sse.handle_post_message(request.scope, receive, send)

        # Combine response
        content = b"".join(response_data)
        logger.debug("Final response prepared", extra={
            "response_length": len(content),
            "response_preview": content[:200].decode('utf-8', errors='replace')
        })

        if not content:
            content = b'{"error": "Empty response from MCP server"}'

        return Response(
            content=content,
            media_type="application/json",
            status_code=response_status
        )
    
    # Create Starlette app
    logger.info("Creating Starlette app...")
    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )
    logger.info("Starlette app created")

    # Run with uvicorn
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Configuring uvicorn server on host=0.0.0.0 port={port}")

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    logger.info("Creating uvicorn.Server instance...")
    server_instance = uvicorn.Server(config)
    logger.info("uvicorn.Server instance created")

    logger.info("Starting uvicorn server...")
    await server_instance.serve()
    logger.info("Server stopped")


def cleanup():
    """
    Cleanup function called on server shutdown.
    """
    close_connector()


if __name__ == "__main__":
    import atexit
    atexit.register(cleanup)
    
    # Determine which mode to run based on environment variable
    transport_mode = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    if transport_mode == "http" or transport_mode == "sse":
        print(f"Starting MCP server in HTTP/SSE mode on port {os.getenv('PORT', '8080')}...")
        asyncio.run(http_main())
    else:
        print("Starting MCP server in stdio mode...")
        asyncio.run(stdio_main())
