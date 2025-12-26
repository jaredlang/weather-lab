"""
Forecast Storage MCP Server

A Model Context Protocol server for storing weather forecasts in Google Cloud SQL.
Provides tools for:
- Uploading forecasts (text + audio) with unicode support
- Retrieving cached forecasts
- Storage statistics and cleanup

Supports full internationalization with all unicode languages.
"""

__version__ = "0.1.0"
