"""
Quick test to verify MCP server is running and responding.
"""
import asyncio
import httpx


async def test_server():
    """Test if MCP server is reachable."""
    server_url = "http://localhost:8080"

    print(f"Testing connection to MCP server at {server_url}...")

    try:
        async with httpx.AsyncClient() as client:
            # Try to connect to the SSE endpoint
            response = await client.get(f"{server_url}/sse", timeout=5.0)
            print(f"✅ Server is reachable! Status: {response.status_code}")
            return True
    except httpx.ConnectError:
        print(f"❌ Cannot connect to server at {server_url}")
        print("   Make sure the MCP server is running:")
        print("   cd forecast_storage_mcp && python server.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_server())
