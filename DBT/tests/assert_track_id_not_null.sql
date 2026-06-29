-- Every silver row should have a Spotify track id

SELECT *
FROM {{ ref('silver_tracks') }}
WHERE track_id IS NULL
