"""
Integration test for weather agent with MCP forecast storage.

This test verifies that the weather agent can properly interact with
the forecast storage MCP server through the client wrapper functions.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_agent_imports():
    """Test that agent can import MCP wrapper functions."""
    try:
        from weather_agent.agent import root_agent
        print("✓ Agent imported successfully")
        
        # Check that the agent has the correct tools
        tool_names = [tool.__name__ for tool in root_agent.tools]
        print(f"✓ Agent tools: {tool_names}")
        
        expected_tools = [
            'get_current_timestamp',
            'set_session_value',
            'get_cached_forecast_from_storage',
            'upload_forecast_to_storage',
            'get_storage_stats_from_mcp'
        ]
        
        for expected in expected_tools:
            if expected in tool_names:
                print(f"  ✓ {expected} is registered")
            else:
                print(f"  ✗ {expected} is MISSING")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wrapper_functions():
    """Test that wrapper functions can be called directly."""
    try:
        from weather_agent.forecast_storage_client import (
            get_cached_forecast_from_storage,
            upload_forecast_to_storage,
            get_storage_stats_from_mcp
        )
        print("✓ Wrapper functions imported successfully")
        
        # Create a mock tool context
        class MockToolContext:
            def __init__(self):
                self.state = {}
        
        mock_context = MockToolContext()
        
        # Test 1: Check cache for non-existent city
        print("\nTest 1: Check cache for non-existent city")
        result = get_cached_forecast_from_storage(mock_context, "NonExistentCity123")
        print(f"  Result: {result}")
        if result.get('cached') == False:
            print("  ✓ Cache miss handled correctly")
        else:
            print("  ✗ Unexpected cache hit")
            return False
        
        # Test 2: Get storage stats
        print("\nTest 2: Get storage stats")
        result = get_storage_stats_from_mcp(mock_context)
        print(f"  Result: {result}")
        if 'status' in result or 'total_forecasts' in result:
            print("  ✓ Storage stats retrieved")
        else:
            print("  ✗ Stats retrieval failed")
            return False
        
        # Test 3: Upload forecast (with fake data)
        print("\nTest 3: Upload forecast (simulated)")
        test_city = "TestCity"
        test_text = "Test forecast text for integration testing"
        test_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
        
        # Create a temporary test audio file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.wav', delete=False) as f:
            f.write("fake audio data")
            temp_audio_path = f.name
        
        try:
            # mock the session state
            mock_context.state['CITY'] = test_city
            mock_context.state['FORECAST_TEXT'] = test_text
            mock_context.state['FORECAST_AUDIO'] = temp_audio_path
            mock_context.state['FORECAST_TIMESTAMP'] = test_timestamp
            # Call upload function
            asyncio.run(upload_forecast_to_storage(
                mock_context
            ))
            print(f"  ✓ Upload function called")
        finally:
            # Cleanup temp file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
        
        # Test 4: Verify cached forecast retrieval (only if upload succeeded)
        print("\nTest 4: Verify cached forecast retrieval")
        result = get_cached_forecast_from_storage(mock_context, test_city)
        print(f"  Result keys: {list(result.keys())}")
        
        if result.get('cached') == True:
            print("  ✓ Cache hit - forecast was successfully uploaded and retrieved")
            
            # Verify forecast text matches
            if result.get('forecast_text') == test_text:
                print("  ✓ Forecast text matches uploaded data")
            else:
                print(f"  ⚠ Forecast text mismatch:")
                print(f"    Expected: {test_text}")
                print(f"    Got: {result.get('forecast_text')}")
            
            # Check audio filepath
            if result.get('audio_filepath'):
                print(f"  ✓ Audio file retrieved: {result.get('audio_filepath')}")
            else:
                print("  ⚠ No audio filepath in cache result")
            
            # Check timestamps
            if result.get('forecast_at'):
                print(f"  ✓ Forecast timestamp: {result.get('forecast_at')}")
            if result.get('expires_at'):
                print(f"  ✓ Expires at: {result.get('expires_at')}")
        else:
            print("  ✗ Cache miss - uploaded forecast not found")
            print(f"    This could indicate the upload didn't persist or TTL expired")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Weather Agent MCP Integration Tests")
    print("=" * 60)
    
    results = []
    
    print("\n[1/2] Testing agent imports and configuration...")
    results.append(test_agent_imports())
    
    print("\n[2/2] Testing wrapper functions...")
    results.append(test_wrapper_functions())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
