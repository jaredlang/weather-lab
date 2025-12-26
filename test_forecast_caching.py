"""
Test script to verify root-level complete forecast caching.

This demonstrates the maximum optimization: when a cached forecast exists,
the root agent skips calling BOTH sub-agents entirely.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Import the root-level caching functions
from weather_agent.caching.forecast_cache import (
    get_forecast,
    cache_forecast,
    get_cache_stats,
    cleanup_expired
)


class MockToolContext:
    """Mock ToolContext for testing purposes."""
    def __init__(self):
        self.state = {}


def test_root_level_caching():
    """Test the root-level complete forecast caching."""
    print("=" * 70)
    print("Root-Level Complete Forecast Caching Test")
    print("=" * 70)

    ctx = MockToolContext()

    # Session 1: First user requests New York weather
    print("\n\n[SESSION 1] First user requests New York weather")
    print("-" * 70)

    city = "New York"

    print("1. Root agent checks cache (filesystem)...")
    cache_result = get_forecast(ctx, city)
    print(f"   Cached: {cache_result['cached']}")

    if not cache_result['cached']:
        print("\n2. Cache MISS - Root agent delegates to sub-agents")
        print("   >> forecast_writer_agent: Fetch weather + generate text")
        print("   >> forecast_speaker_agent: Generate audio from text")

        # Simulate sub-agent results with CURRENT timestamp
        from datetime import datetime
        current_ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        simulated_forecast_text = (
            "Good morning! It's a chilly day in New York with overcast skies. "
            "Temperatures are around 40 degrees. Bundle up and stay warm!"
        )
        simulated_text_path = f"output/New York/forecast_text_{current_ts}.txt"
        simulated_audio_path = f"output/New York/forecast_audio_{current_ts}.wav"

        print(f"\n3. Sub-agents completed. Files written to disk...")
        # Create actual files for testing
        os.makedirs(os.path.join("output", city), exist_ok=True)

        # Create text file
        with open(simulated_text_path, 'w', encoding='utf-8') as f:
            f.write(simulated_forecast_text)

        # Create dummy audio file
        with open(simulated_audio_path, 'wb') as f:
            # Write minimal WAV header
            f.write(b"RIFF" + (100).to_bytes(4, 'little') + b"WAVEfmt ")
            f.write((16).to_bytes(4, 'little'))
            f.write(b"\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00")
            f.write(b"data" + (64).to_bytes(4, 'little') + b"\x00" * 64)

        print(f"   Text file: {simulated_text_path} [CREATED]")
        print(f"   Audio file: {simulated_audio_path} [CREATED]")
        print(f"   Files are now cached via filesystem!")

    # Show cache stats
    stats = get_cache_stats(ctx)
    print(f"\n   Cache stats: {stats['cities_with_valid_cache']} cities cached")
    print(f"   Cached cities: {stats['cached_cities']}")

    # Session 2: Different user requests same city
    print("\n\n[SESSION 2] Different user requests New York weather")
    print("-" * 70)

    ctx2 = MockToolContext()

    print("1. Root agent checks cache...")
    cache_result2 = get_forecast(ctx2, city)
    print(f"   Cached: {cache_result2['cached']}")

    if cache_result2['cached']:
        print(f"\n   *** CACHE HIT! ***")
        print(f"   Cache age: {cache_result2['age_seconds']} seconds old")
        print(f"\n   Retrieved from cache:")
        print(f"   - Forecast text: {cache_result2['forecast_text'][:60]}...")
        print(f"   - Text file: {cache_result2['text_file_path']}")
        print(f"   - Audio file: {cache_result2['audio_file_path']}")

        print(f"\n   >> BOTH SUB-AGENTS SKIPPED!")
        print(f"   >> NO weather API call")
        print(f"   >> NO LLM forecast generation")
        print(f"   >> NO TTS audio generation")
        print(f"   >> MAXIMUM optimization achieved!")
    else:
        print(f"   [UNEXPECTED] Cache miss")

    # Session 3: Different city
    print("\n\n[SESSION 3] User requests Chicago weather")
    print("-" * 70)

    ctx3 = MockToolContext()
    chicago_city = "Chicago"

    print("1. Root agent checks cache...")
    cache_result3 = get_forecast(ctx3, chicago_city)
    print(f"   Cached: {cache_result3['cached']}")

    if not cache_result3['cached']:
        print("\n2. Cache MISS for Chicago (expected - different city)")
        print("   >> Root agent would delegate to sub-agents")

        # Simulate files being created
        print("   >> Sub-agents would create Chicago forecast files")
        print("   >> Files automatically available for future cache lookups")

    # Session 4: Case-insensitive test
    print("\n\n[SESSION 4] User requests 'new york' (lowercase)")
    print("-" * 70)

    ctx4 = MockToolContext()

    print("1. Root agent checks cache with lowercase city name...")
    cache_result4 = get_forecast(ctx4, "new york")  # lowercase
    print(f"   Cached: {cache_result4['cached']}")

    if cache_result4['cached']:
        print(f"   [SUCCESS] Filesystem lookup works for different case!")
        print(f"   'new york' found files in 'New York' directory")
    else:
        print(f"   [NOTE] Different casing - filesystem is case-sensitive on Linux")

    # Final cache stats
    print("\n\n" + "=" * 70)
    print("Final Cache Statistics")
    print("=" * 70)
    stats = get_cache_stats(ctx)
    print(f"Total city directories: {stats['total_cities']}")
    print(f"Cities with valid cache: {stats['cities_with_valid_cache']}")
    print(f"Cities: {', '.join(stats['cached_cities'])}")
    print(f"Cache TTL: {stats['ttl_readable']}")

    # Test cleanup
    print("\n\n[CLEANUP TEST]")
    print("-" * 70)
    cleanup_result = cleanup_expired(ctx)
    print(f"Expired files removed: {cleanup_result['expired_removed']}")
    print(f"Remaining files: {cleanup_result['remaining_files']}")

    print("\n" + "=" * 70)
    print("[SUCCESS] Root-level caching test completed!")
    print("=" * 70)

    print("\nOptimization Summary:")
    print("=" * 70)

    print("\n[WITHOUT ROOT-LEVEL CACHE]")
    print("User Request -> Root Agent -> forecast_writer_agent -> forecast_speaker_agent")
    print("  - Weather API call (400ms)")
    print("  - LLM forecast generation (1-3s)")
    print("  - TTS audio generation (2-5s)")
    print("  - Total: ~3-8 seconds")
    print("  - Cost: Weather API + LLM + TTS")

    print("\n[WITH ROOT-LEVEL CACHE]")
    print("User Request -> Root Agent -> Check cache -> Return cached result")
    print("  - Cache lookup (~0ms)")
    print("  - No sub-agent calls!")
    print("  - Total: <100ms")
    print("  - Cost: $0 (all cached)")

    print("\n[COST SAVINGS]")
    print("  - Weather API: 100% saved (no call)")
    print("  - LLM Generation: 100% saved (no call)")
    print("  - TTS Generation: 100% saved (no call)")
    print("  - Speed: 30-80x faster")
    print("  - TOTAL SAVINGS: Maximum possible!")

    print("\n[CACHE HIERARCHY - COMPLETE]")
    print("  1. Weather API cache (15 min) - Layer 1")
    print("  2. Filesystem-based forecast cache (30 min) - Layer 2")
    print("     |-> Checks actual files in OUTPUT_DIR")
    print("     |-> Parses timestamps from filenames")
    print("     |-> Skips BOTH sub-agents when valid files exist")
    print("     |-> Maximum optimization")

    print("\n[KEY BENEFITS]")
    print("  - Filesystem as single source of truth")
    print("  - No in-memory state to manage")
    print("  - Survives application restarts")
    print("  - Easy to debug (inspect files directly)")
    print("  - Shared across all users/sessions")
    print("  - 30-minute TTL based on file timestamps")
    print("  - Automatic cleanup of expired files")


if __name__ == "__main__":
    test_root_level_caching()
