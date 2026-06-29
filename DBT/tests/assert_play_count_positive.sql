-- Every gold summary row should have at least one play

SELECT *
FROM {{ ref('gold_daily_summary') }}
WHERE total_play_count = 0
