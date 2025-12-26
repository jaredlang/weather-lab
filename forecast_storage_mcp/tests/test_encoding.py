"""
Unit tests for encoding module.

These tests can run without database connection.

Usage:
    python -m pytest tests/test_encoding.py
    # or
    python tests/test_encoding.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.encoding import encode_text, decode_text, detect_optimal_encoding


def test_english_text():
    """Test standard English text encoding/decoding."""
    text = "Weather in Chicago: Sunny with temperatures around 75°F"
    encoded, size, enc = encode_text(text)
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Text should match after encode/decode"
    assert enc == 'utf-8', "English should use utf-8"
    assert size > 0, "Size should be positive"
    print(f"✅ English test passed (size: {size} bytes)")


def test_spanish_text():
    """Test Spanish text with accents."""
    text = "El clima en México: Soleado, 24°C. Mañana será nublado."
    encoded, size, enc = encode_text(text)
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Spanish text should match after encode/decode"
    print(f"✅ Spanish test passed (size: {size} bytes)")


def test_chinese_text():
    """Test Chinese characters with utf-16."""
    text = "北京天气：晴朗，摄氏24度。明天将有雨。"
    encoded, size, enc = encode_text(text, encoding='utf-16')
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Chinese text should match after encode/decode"
    assert enc == 'utf-16', "Chinese should use utf-16 when specified"
    print(f"✅ Chinese test passed (size: {size} bytes)")


def test_japanese_text():
    """Test Japanese text (mixed Hiragana, Katakana, Kanji)."""
    text = "東京の天気：晴れ、摂氏24度です。明日は曇りでしょう。"
    encoded, size, enc = encode_text(text, encoding='utf-16')
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Japanese text should match after encode/decode"
    print(f"✅ Japanese test passed (size: {size} bytes)")


def test_arabic_text():
    """Test Arabic text (RTL)."""
    text = "الطقس في دبي: مشمس، 35 درجة مئوية. غداً سيكون غائماً."
    encoded, size, enc = encode_text(text)
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Arabic text should match after encode/decode"
    print(f"✅ Arabic test passed (size: {size} bytes)")


def test_emoji_text():
    """Test text with emoji."""
    text = "Weather: ☀️ Sunny, 🌡️ 75°F, 💨 Light breeze, 💧 No rain"
    encoded, size, enc = encode_text(text)
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Emoji text should match after encode/decode"
    print(f"✅ Emoji test passed (size: {size} bytes)")


def test_mixed_scripts():
    """Test mixed scripts in one text."""
    text = "多语言天气 Multilingual Weather Прогноз погоды الطقس ☀️"
    encoded, size, enc = encode_text(text)
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Mixed scripts should match after encode/decode"
    print(f"✅ Mixed scripts test passed (size: {size} bytes)")


def test_encoding_detection():
    """Test optimal encoding detection."""
    # ASCII/Latin text -> utf-8
    assert detect_optimal_encoding("Hello world") == 'utf-8'
    print("✅ ASCII encoding detection: utf-8")
    
    # Heavy CJK text -> utf-16
    assert detect_optimal_encoding("北京天气预报明天晴朗温度适宜") == 'utf-16'
    print("✅ CJK encoding detection: utf-16")
    
    # Mixed text -> utf-8 (default)
    assert detect_optimal_encoding("Hola 你好 world") == 'utf-8'
    print("✅ Mixed encoding detection: utf-8")


def test_long_text():
    """Test encoding/decoding of longer text."""
    text = "Weather forecast for Chicago. " * 100  # 3000+ chars
    encoded, size, enc = encode_text(text)
    decoded = decode_text(encoded, enc)
    
    assert text == decoded, "Long text should match after encode/decode"
    assert size >= 3000, "Size should reflect long text"
    print(f"✅ Long text test passed (size: {size} bytes)")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  ENCODING MODULE TESTS")
    print("=" * 60)
    print()
    
    tests = [
        test_english_text,
        test_spanish_text,
        test_chinese_text,
        test_japanese_text,
        test_arabic_text,
        test_emoji_text,
        test_mixed_scripts,
        test_encoding_detection,
        test_long_text
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All encoding tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
