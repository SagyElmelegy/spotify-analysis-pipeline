{{ config(
    materialized='table',
    schema='silver'
) }}

-- Clean up raw JSON from S3 into one row per track play
SELECT
    value:item:id::STRING AS track_id,
    value:item:name::STRING AS track_name,
    value:item:artists[0]:name::STRING AS artist_name,
    value:item:album:name::STRING AS album_name,
    TO_TIMESTAMP_NTZ(value:timestamp::NUMBER / 1000) AS played_at,
    value:item:duration_ms::INT AS duration_ms,
    CURRENT_TIMESTAMP() AS ingestion_timestamp
FROM {{ source('raw', 'spotify_bronze_raw') }}
WHERE value:item IS NOT NULL
