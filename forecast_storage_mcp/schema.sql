-- Forecasts table with full internationalization support
-- Stores weather forecasts with binary text and audio storage
-- Supports all unicode languages and compression

CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city VARCHAR(100) NOT NULL,
    forecast_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Binary storage for text and audio
    forecast_text BYTEA NOT NULL,  -- Compressed unicode text
    audio_file BYTEA,                     -- Binary audio data
    
    -- File metadata
    text_size_bytes INTEGER NOT NULL,          -- Text size in bytes
    audio_size_bytes INTEGER,                  -- Audio file size
    
    -- Unicode & Internationalization support
    text_encoding VARCHAR(20) DEFAULT 'utf-8' NOT NULL,  -- utf-8, utf-16, utf-32
    text_language VARCHAR(10),                -- ISO 639-1 code: 'en', 'es', 'fr', 'ja', 'zh', etc.
    text_locale VARCHAR(20),                  -- Full locale: 'en-US', 'es-MX', 'zh-CN', etc.
    
    -- Audio metadata
    audio_format VARCHAR(10) DEFAULT 'wav',
    audio_language VARCHAR(10),               -- Language of spoken audio
    
    -- Flexible metadata
    metadata JSONB,  -- Store additional i18n info, character counts, etc.
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_city_expires ON forecasts(city, expires_at DESC);
CREATE INDEX IF NOT EXISTS idx_expires_cleanup ON forecasts(expires_at);
CREATE INDEX IF NOT EXISTS idx_forecast_at ON forecasts(forecast_at DESC);
CREATE INDEX IF NOT EXISTS idx_language ON forecasts(text_language);  -- Query by language
CREATE INDEX IF NOT EXISTS idx_locale ON forecasts(text_locale);      -- Query by locale

-- Enable auto-vacuum for efficient storage management
ALTER TABLE forecasts SET (autovacuum_enabled = true);

-- Storage statistics with encoding info
CREATE OR REPLACE FUNCTION get_storage_stats()
RETURNS TABLE(
    total_forecasts BIGINT,
    total_text_bytes BIGINT,
    total_audio_bytes BIGINT,
    encodings_used JSONB,
    languages_used JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)::BIGINT FROM forecasts),
        (SELECT COALESCE(SUM(text_size_bytes), 0)::BIGINT FROM forecasts),
        (SELECT COALESCE(SUM(audio_size_bytes), 0)::BIGINT FROM forecasts),
        (SELECT jsonb_object_agg(COALESCE(text_encoding, 'unknown'), encoding_count)
         FROM (
             SELECT text_encoding, COUNT(*) as encoding_count
             FROM forecasts
             WHERE text_encoding IS NOT NULL
             GROUP BY text_encoding
         ) enc),
        (SELECT jsonb_object_agg(COALESCE(text_language, 'unknown'), language_count)
         FROM (
             SELECT text_language, COUNT(*) as language_count
             FROM forecasts
             WHERE text_language IS NOT NULL
             GROUP BY text_language
         ) lang);
END;
$$ LANGUAGE plpgsql;

-- Query forecasts by language
CREATE OR REPLACE FUNCTION get_forecasts_by_language(
    lang VARCHAR(10),
    city_filter VARCHAR(100) DEFAULT NULL
)
RETURNS TABLE(
    forecast_id UUID,
    city VARCHAR,
    forecast_text TEXT,
    forecast_at TIMESTAMPTZ,
    text_locale VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.city,
        convert_from(f.forecast_text, f.text_encoding)::TEXT,
        f.forecast_at,
        f.text_locale
    FROM forecasts f
    WHERE f.text_language = lang
      AND f.expires_at > NOW()
      AND (city_filter IS NULL OR f.city = city_filter)
    ORDER BY f.forecast_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Cleanup function for expired forecasts
CREATE OR REPLACE FUNCTION cleanup_expired_forecasts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM forecasts
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
