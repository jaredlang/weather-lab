"""
MCP Server for Forecast Storage

Exposes weather forecast storage operations as MCP tools.
Provides upload, retrieval, cleanup, and statistics for forecasts stored in Cloud SQL.
"""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent

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
                    "audio_file_path": {
                        "type": "string",
                        "description": "Path to audio WAV file to upload"
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
                "required": ["city", "forecast_text", "audio_file_path", "forecast_at"]
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
    try:
        # Route to appropriate function
        if name == "upload_forecast":
            result = upload_forecast(
                city=arguments["city"],
                forecast_text=arguments["forecast_text"],
                audio_file_path=arguments["audio_file_path"],
                timestamp=arguments["forecast_at"],
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
        
        # Return result as JSON
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    except Exception as e:
        # Handle unexpected errors
        error_result = {
            "status": "error",
            "message": f"Tool execution failed: {str(e)}"
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


async def main():
    """
    Main entry point for the MCP server.
    """
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def cleanup():
    """
    Cleanup function called on server shutdown.
    """
    close_connector()


if __name__ == "__main__":
    import atexit
    atexit.register(cleanup)
    asyncio.run(main())
