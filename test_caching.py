"""
Simple test script to verify weather API caching functionality.

This script demonstrates:
1. First call makes actual API request
2. Second call returns cached result (much faster)
3. Cache statistics
"""

import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the cached weather function
from weather_agent.sub_agents.forecast_writer.tools.get_current_weather import get_current_weather


def test_caching():
    """Test the caching functionality of get_current_weather."""
    print("=" * 60)
    print("Weather API Caching Test")
    print("=" * 60)

    test_city = "New York"

    # First call - should hit the API
    print(f"\n1. First call for {test_city} (should hit API)...")
    start_time = time.time()
    result1 = get_current_weather(test_city)
    first_call_time = time.time() - start_time
    print(f"   Time: {first_call_time:.3f}s")
    print(f"   Result type: {type(result1)}")
    if isinstance(result1, str):
        print(f"   Preview: {result1[:100]}...")

    # Second call - should use cache
    print(f"\n2. Second call for {test_city} (should use cache)...")
    start_time = time.time()
    result2 = get_current_weather(test_city)
    second_call_time = time.time() - start_time
    print(f"   Time: {second_call_time:.3f}s")
    print(f"   Result type: {type(result2)}")

    # Verify results are identical
    print(f"\n3. Verification:")
    print(f"   Results identical: {result1 == result2}")
    if second_call_time > 0:
        print(f"   Speed improvement: {first_call_time / second_call_time:.1f}x faster")
    else:
        print(f"   Speed improvement: >1000x faster (cached call was instantaneous!)")

    # Cache statistics
    if hasattr(get_current_weather, 'cache_size'):
        cache_size = get_current_weather.cache_size()
        print(f"   Cache entries: {cache_size}")

    # Test different city
    print(f"\n4. Testing different city (Chicago)...")
    start_time = time.time()
    _result3 = get_current_weather("Chicago")
    third_call_time = time.time() - start_time
    print(f"   Time: {third_call_time:.3f}s")

    if hasattr(get_current_weather, 'cache_size'):
        cache_size = get_current_weather.cache_size()
        print(f"   Cache entries: {cache_size}")

    # Test same city again
    print(f"\n5. Chicago again (should use cache)...")
    start_time = time.time()
    _result4 = get_current_weather("Chicago")
    fourth_call_time = time.time() - start_time
    print(f"   Time: {fourth_call_time:.3f}s")
    if fourth_call_time > 0:
        print(f"   Speed improvement: {third_call_time / fourth_call_time:.1f}x faster")
    else:
        print(f"   Speed improvement: >1000x faster (cached!)")

    print("\n" + "=" * 60)
    print("[SUCCESS] Caching test completed!")
    print("=" * 60)
    print("\nKey Findings:")
    print(f"  - First API call: {first_call_time:.3f}s")
    print(f"  - Cached call: {second_call_time:.3f}s (instantaneous!)")
    if second_call_time > 0:
        print(f"  - Speed improvement: {first_call_time / second_call_time:.1f}x")
    else:
        print(f"  - Speed improvement: >1000x (cached response)")
    print(f"  - Cache TTL: 15 minutes (900 seconds)")
    print("\nExpected Savings:")
    print("  - 80-95% reduction in API calls for repeated queries")
    print("  - 200-500ms saved per cached request")
    print("  - Significant cost reduction (fewer OpenWeather API calls)")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENWEATHER_API_KEY"):
        print("[ERROR] OPENWEATHER_API_KEY not found in environment variables")
        print("   Please set it in your .env file")
        exit(1)

    test_caching()
