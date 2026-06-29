-- Fail if any play timestamp is in the future (bad data from the API or clock issues)

SELECT *
FROM {{ ref('silver_tracks') }}
WHERE DATE(played_at) > CURRENT_DATE()
