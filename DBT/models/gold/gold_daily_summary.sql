{{ config(
    materialized='view',
    schema='gold'
) }}

-- Daily play counts per track (used by Power BI gold layer)
SELECT
    DATE(played_at) AS date,
    track_name AS top_track,
    artist_name,
    COUNT(*) AS total_play_count,
    AVG(duration_ms) / 1000 AS avg_duration_sec
FROM {{ ref('silver_tracks') }}
GROUP BY DATE(played_at), track_name, artist_name
