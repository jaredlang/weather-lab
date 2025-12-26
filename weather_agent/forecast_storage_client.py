"""
MCP Client Wrapper for Forecast Storage.

Provides simple functions for the weather agent to interact with the
forecast storage MCP server without dealing with MCP protocol details.
"""

import os
import json
import subprocess
import asyncio
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext

import logging
import google.cloud.logging

from weather_agent.write_file import write_audio_file
from weather_agent.caching.forecast_file_cleanup import cleanup_old_forecast_files_async

# Path to MCP server
MCP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "forecast_storage_mcp",
    "server.py"
)


def _call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Internal helper to call MCP server tool.

    Args:
        tool_name: Name of the MCP tool to call
        arguments: Tool arguments as dictionary

    Returns:
        Tool result as dictionary
    """
    try:
        # For now, we'll import and call directly since MCP client integration
        # with ADK is complex. In production, use proper MCP client.

        # Import MCP server operations directly
        import sys
        mcp_dir = os.path.dirname(MCP_SERVER_PATH)

        # Add parent directory to enable package imports
        if mcp_dir not in sys.path:
            sys.path.insert(0, mcp_dir)

        # Import as package to support relative imports
        from forecast_storage_mcp.tools.forecast_operations import (
            upload_forecast,
            get_cached_forecast,
            get_storage_stats,
            cleanup_expired_forecasts,
            list_forecasts
        )
        from forecast_storage_mcp.tools.connection import test_connection

        # Route to appropriate function
        if tool_name == "upload_forecast":
            return upload_forecast(**arguments)
        elif tool_name == "get_cached_forecast":
            return get_cached_forecast(**arguments)
        elif tool_name == "get_storage_stats":
            return get_storage_stats()
        elif tool_name == "cleanup_expired_forecasts":
            return cleanup_expired_forecasts()
        elif tool_name == "list_forecasts":
            return list_forecasts(**arguments)
        elif tool_name == "test_connection":
            return test_connection()
        else:
            return {
                "status": "error",
                "message": f"Unknown tool: {tool_name}"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"MCP tool call failed: {str(e)}"
        }


async def upload_forecast_to_storage(
    callback_context: CallbackContext
) -> None:
    """
    Upload complete forecast (text + audio) to Cloud SQL storage.
    
    This is an ADK tool that wraps the MCP upload_forecast tool.
    
    Args:
        callback_context: Agent callback context
    
    Returns:
        None
    """
    city = callback_context.state["CITY"]
    forecast_text = callback_context.state["FORECAST_TEXT"]
    audio_file_path = callback_context.state["FORECAST_AUDIO"]
    forecast_at = callback_context.state["FORECAST_TIMESTAMP"]
    ttl_minutes = 30  # Default TTL in minutes

    result = _call_mcp_tool("upload_forecast", {
        "city": city,
        "forecast_text": forecast_text,
        "audio_file_path": audio_file_path,
        "forecast_at": forecast_at,
        "ttl_minutes": ttl_minutes,
        "language": "en",  # Could be made configurable
        "locale": "en-US"
    })
    
    # callback doesn't support any return. Use logging instead.
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()

    if result.get("status") == "success":
        logging.info({
            "status": "success",
            "message": f"Forecast uploaded to Cloud SQL storage",
            "forecast_id": result.get("forecast_id", ""),
            "storage_info": json.dumps(result.get("sizes", {}))
        })
        
        # Fire-and-forget async cleanup (no await, no return value needed)
        # This runs in the background and doesn't block the upload response
        asyncio.create_task(cleanup_old_forecast_files_async())
    else:
        logging.error({
            "status": "error",
            "message": f"Upload failed: {result.get('message', 'Unknown error')}"
        })


def get_cached_forecast_from_storage(
    tool_context: ToolContext,
    city: str
) -> Dict[str, Any]:
    """
    Retrieve cached forecast from Cloud SQL storage if available.
    
    This is an ADK tool that wraps the MCP get_cached_forecast tool.
    
    Args:
        tool_context: ADK tool context
        city: City name to check
    
    Returns:
        Dictionary with cache status and forecast data if cached
    """
    result = _call_mcp_tool("get_cached_forecast", {
        "city": city
    })
    
    if result.get("cached"):
        # Cache hit - return forecast data
        # store audio_data into a file using write_audio_file tool
        audio_file = write_audio_file(tool_context, city, result.get("audio_data", ""))

        return {
            "cached": True,
            "forecast_text": result.get("forecast_text", ""),
            "audio_filepath": audio_file.get("file_path", None),
            "age_seconds": result.get("age_seconds", 0),
            "forecast_at": result.get("forecast_at", ""),
            "expires_at": result.get("expires_at", ""),
        }
    else:
        # Cache miss
        return {
            "cached": False,
            "forecast_text": None,
            "audio_filepath": None,
        }


def get_storage_stats_from_mcp(
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Get storage statistics from Cloud SQL.
    
    This is an ADK tool that wraps the MCP get_storage_stats tool.
    
    Args:
        tool_context: ADK tool context
    
    Returns:
        Dictionary with storage statistics
    """
    result = _call_mcp_tool("get_storage_stats", {})
    
    if result.get("status") == "success":
        return {
            "status": "success",
            "total_forecasts": result.get("total_forecasts", 0),
            "total_text_bytes": result.get("total_text_bytes", 0),
            "total_audio_bytes": result.get("total_audio_bytes", 0),
            "city_breakdown": json.dumps(result.get("city_breakdown", []))
        }
    else:
        return {
            "status": "error",
            "message": result.get("message", "Failed to get stats")
        }


def test_storage_connection(
    tool_context: ToolContext
) -> Dict[str, str]:
    """
    Test connection to Cloud SQL storage.
    
    This is an ADK tool that wraps the MCP test_connection tool.
    
    Args:
        tool_context: ADK tool context
    
    Returns:
        Dictionary with connection status
    """
    result = _call_mcp_tool("test_connection", {})
    
    if result.get("status") == "success":
        return {
            "status": "connected",
            "message": f"Connected to {result.get('instance', 'Cloud SQL')}",
            "database": result.get("database", ""),
            "table_exists": str(result.get("forecasts_table_exists", False))
        }
    else:
        return {
            "status": "error",
            "message": f"Connection failed: {result.get('error', 'Unknown error')}"
        }
