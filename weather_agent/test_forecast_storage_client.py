"""
Test script for forecast storage client wrapper.

Tests the MCP client wrapper functions that the weather agent will use.
Run this after setting up Cloud SQL and environment variables.

Usage:
    python test_forecast_storage_client.py
"""

import os
import tempfile
import wave
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from forecast_storage_mcp
mcp_env_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "forecast_storage_mcp",
    ".env"
)
if os.path.exists(mcp_env_path):
    load_dotenv(mcp_env_path)

# Mock ToolContext for testing
class MockToolContext:
    """Mock ADK ToolContext for testing."""
    def __init__(self):
        self.state = {}

from forecast_storage_client import (
    upload_forecast_to_storage,
    get_cached_forecast_from_storage,
    get_storage_stats_from_mcp,
    test_storage_connection
)


def create_test_audio_file():
    """Create a temporary WAV file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False)
    
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(24000)  # 24kHz
        # Write 1 second of silence
        wf.writeframes(b'\x00\x00' * 24000)
    
    return temp_file.name


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(result):
    """Print result in a readable format."""
    import json
    print(json.dumps(result, indent=2, default=str))


def test_1_connection():
    """Test storage connection via wrapper."""
    print_section("TEST 1: Test Storage Connection")
    
    tool_context = MockToolContext()
    
    print("\nTesting connection through wrapper...")
    result = test_storage_connection(tool_context)
    print_result(result)
    
    if result.get('status') == 'connected':
        print("\n[PASS] Connection test passed!")
        if result.get('table_exists') == 'False':
            print("\n[WARN] WARNING: forecasts table does not exist!")
            print("   Please apply schema.sql first")
            return False
        return True
    else:
        print("\n[FAIL] Connection test failed!")
        print("   Check Cloud SQL configuration in forecast_storage_mcp/.env")
        return False


def test_2_upload_wrapper():
    """Test upload forecast via wrapper."""
    print_section("TEST 2: Upload Forecast (Wrapper)")
    
    tool_context = MockToolContext()
    
    # Create test audio file
    audio_file = create_test_audio_file()
    
    try:
        city = "test_chicago"
        forecast_text = "Test forecast: Sunny, 75F. Perfect weather for testing!"
        timestamp = datetime.now(timezone.utc).isoformat()
        
        print(f"\nUploading via wrapper for {city}...")
        print(f"Text: {forecast_text[:50]}...")
        
        result = upload_forecast_to_storage(
            tool_context=tool_context,
            city=city,
            forecast_text=forecast_text,
            audio_file_path=audio_file,
            timestamp=timestamp,
            ttl_minutes=30
        )
        
        print_result(result)
        
        if result.get('status') == 'success':
            print("\n[PASS] Upload wrapper test passed!")
            print(f"   Forecast ID: {result.get('forecast_id', 'N/A')}")
            return True
        else:
            print("\n[FAIL] Upload wrapper test failed!")
            return False
            
    finally:
        # Cleanup temp file
        if os.path.exists(audio_file):
            os.unlink(audio_file)


def test_3_get_cached_wrapper():
    """Test get cached forecast via wrapper."""
    print_section("TEST 3: Get Cached Forecast (Wrapper)")
    
    tool_context = MockToolContext()
    city = "test_chicago"
    
    print(f"\nRetrieving cached forecast via wrapper for {city}...")
    
    result = get_cached_forecast_from_storage(
        tool_context=tool_context,
        city=city
    )
    
    print_result(result)
    
    if result.get('cached'):
        print("\n[PASS] Get cached wrapper test passed!")
        print(f"   Forecast age: {result.get('age_seconds', 0)} seconds")
        print(f"   Text length: {len(result.get('forecast_text', ''))} characters")
        return True
    else:
        print("\n[INFO] No cached forecast found (OK if no forecast was uploaded)")
        return True  # Not an error


def test_4_stats_wrapper():
    """Test get storage stats via wrapper."""
    print_section("TEST 4: Get Storage Stats (Wrapper)")
    
    tool_context = MockToolContext()
    
    print("\nRetrieving storage stats via wrapper...")
    
    result = get_storage_stats_from_mcp(tool_context)
    print_result(result)
    
    if result.get('status') == 'success':
        print("\n[PASS] Stats wrapper test passed!")
        print(f"   Total forecasts: {result.get('total_forecasts', 0)}")
        print(f"   Total text bytes: {result.get('total_text_bytes', 0)}")
        print(f"   Total audio bytes: {result.get('total_audio_bytes', 0)}")
        return True
    else:
        print("\n[FAIL] Stats wrapper test failed!")
        return False


def test_5_full_workflow():
    """Test complete workflow: upload → retrieve → verify."""
    print_section("TEST 5: Full Workflow Test")
    
    tool_context = MockToolContext()
    
    # Create test audio file
    audio_file = create_test_audio_file()
    
    try:
        city = "workflow_test"
        forecast_text = "Workflow test forecast: Cloudy with a chance of testing."
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Step 1: Upload
        print("\nStep 1: Uploading forecast...")
        upload_result = upload_forecast_to_storage(
            tool_context=tool_context,
            city=city,
            forecast_text=forecast_text,
            audio_file_path=audio_file,
            timestamp=timestamp,
            ttl_minutes=30
        )
        
        if upload_result.get('status') != 'success':
            print("[FAIL] Upload failed in workflow test")
            return False

        print(f"[PASS] Upload successful: {upload_result.get('forecast_id')}")
        
        # Step 2: Retrieve
        print("\nStep 2: Retrieving cached forecast...")
        cache_result = get_cached_forecast_from_storage(
            tool_context=tool_context,
            city=city
        )
        
        if not cache_result.get('cached'):
            print("[FAIL] Cache retrieval failed - forecast not found")
            return False

        print(f"[PASS] Cache hit: {cache_result.get('age_seconds')} seconds old")
        
        # Step 3: Verify content
        print("\nStep 3: Verifying content...")
        retrieved_text = cache_result.get('forecast_text', '')
        
        if forecast_text == retrieved_text:
            print("[PASS] Text content matches perfectly!")
        else:
            print("[FAIL] Text content mismatch:")
            print(f"   Expected: {forecast_text}")
            print(f"   Got: {retrieved_text}")
            return False
        
        # Step 4: Check stats
        print("\nStep 4: Checking storage stats...")
        stats_result = get_storage_stats_from_mcp(tool_context)
        
        if stats_result.get('status') == 'success':
            print(f"[PASS] Stats retrieved: {stats_result.get('total_forecasts')} total forecasts")

        print("\n[PASS] Full workflow test passed!")
        return True
        
    finally:
        # Cleanup temp file
        if os.path.exists(audio_file):
            os.unlink(audio_file)


def main():
    """Run all wrapper tests."""
    print("\n" + "=" * 60)
    print("  FORECAST STORAGE CLIENT WRAPPER - TEST SUITE")
    print("=" * 60)
    print("\nThis script tests the MCP client wrapper that the")
    print("weather agent will use to interact with Cloud SQL storage.\n")
    
    # Check environment
    required_vars = [
        "GCP_PROJECT_ID",
        "CLOUD_SQL_INSTANCE",
        "CLOUD_SQL_PASSWORD"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("[FAIL] Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in forecast_storage_mcp/.env")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Connection (required)
    if not test_1_connection():
        print("\n" + "=" * 60)
        print("[FAIL] Connection test failed. Please fix before continuing.")
        print("=" * 60)
        return
    tests_passed += 1
    
    # Test 2: Upload wrapper
    if test_2_upload_wrapper():
        tests_passed += 1
    
    # Test 3: Get cached wrapper
    if test_3_get_cached_wrapper():
        tests_passed += 1
    
    # Test 4: Stats wrapper
    if test_4_stats_wrapper():
        tests_passed += 1
    
    # Test 5: Full workflow
    if test_5_full_workflow():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"\nPassed: {tests_passed}/{total_tests} tests")
    
    if tests_passed == total_tests:
        print("\n[SUCCESS] All wrapper tests passed!")
        print("\nThe MCP client wrapper is working correctly and ready")
        print("to be integrated into the weather agent.")
    elif tests_passed >= 3:
        print("\n[PASS] Core wrapper tests passed.")
        print("\nThe wrapper is functional but some tests failed.")
    else:
        print("\n[WARN] Multiple tests failed. Please review errors above.")
    
    print("\nNext steps:")
    print("1. If all tests pass, update agent.py to use these wrapper functions")
    print("2. Modify generate_audio.py to work with the new storage")
    print("3. Test the full weather agent workflow")


if __name__ == "__main__":
    main()
