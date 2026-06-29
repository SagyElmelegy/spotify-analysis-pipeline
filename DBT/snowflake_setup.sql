# Spotify analytics pipeline — run once in Snowflake as ACCOUNTADMIN.
# After step 1, run DESC INTEGRATION and update the AWS IAM role trust policy.

-- ---------------------------------------------------------------------------
-- 1. Database, schemas, and bronze layer (S3 -> Snowflake)
-- ---------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS spotify;
USE DATABASE spotify;

CREATE SCHEMA IF NOT EXISTS spotify.raw;
CREATE SCHEMA IF NOT EXISTS spotify.silver;
CREATE SCHEMA IF NOT EXISTS spotify.gold;

CREATE OR REPLACE FILE FORMAT spotify.raw.json_format
  TYPE = JSON
  STRIP_OUTER_ARRAY = FALSE;

CREATE OR REPLACE STORAGE INTEGRATION spotify_s3_integration
  TYPE = EXTERNAL
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::070502825836:role/spotify-s3-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://spotify-bronze-data-bucket/bronze/');

-- Copy STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID into AWS, then continue
DESC INTEGRATION spotify_s3_integration;

CREATE OR REPLACE STAGE spotify.raw.spotify_bronze_stage
  URL = 's3://spotify-bronze-data-bucket/bronze/'
  STORAGE_INTEGRATION = spotify_s3_integration
  FILE_FORMAT = spotify.raw.json_format;

CREATE OR REPLACE EXTERNAL TABLE spotify.raw.spotify_bronze_raw
  WITH LOCATION = @spotify.raw.spotify_bronze_stage
  AUTO_REFRESH = TRUE
  FILE_FORMAT = spotify.raw.json_format;


-- ---------------------------------------------------------------------------
-- 2. Permissions for dbt user (SAJY) and troubleshooting (SYSADMIN)
-- ---------------------------------------------------------------------------

GRANT USAGE ON DATABASE spotify TO USER SAJY;
GRANT USAGE ON SCHEMA spotify.raw TO USER SAJY;
GRANT USAGE ON SCHEMA spotify.silver TO USER SAJY;
GRANT USAGE ON SCHEMA spotify.gold TO USER SAJY;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO USER SAJY;
GRANT SELECT ON ALL TABLES IN SCHEMA spotify.raw TO USER SAJY;
GRANT SELECT ON FUTURE TABLES IN SCHEMA spotify.raw TO USER SAJY;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA spotify.silver TO USER SAJY;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA spotify.gold TO USER SAJY;

GRANT USAGE ON DATABASE spotify TO ROLE SYSADMIN;
GRANT USAGE ON SCHEMA spotify.raw TO ROLE SYSADMIN;
GRANT USAGE ON SCHEMA spotify.silver TO ROLE SYSADMIN;
GRANT USAGE ON SCHEMA spotify.gold TO ROLE SYSADMIN;
GRANT USAGE ON STAGE spotify.raw.spotify_bronze_stage TO ROLE SYSADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA spotify.raw TO ROLE SYSADMIN;


-- ---------------------------------------------------------------------------
-- 3. Optional preview view (dbt builds the real silver/gold tables)
-- ---------------------------------------------------------------------------

USE ROLE SYSADMIN;
USE DATABASE spotify;
USE SCHEMA spotify.silver;

DROP VIEW IF EXISTS spotify.silver.tracks_view;
DROP TABLE IF EXISTS spotify.silver.tracks;
DROP TABLE IF EXISTS spotify.gold.daily_summary;

CREATE OR REPLACE VIEW spotify.silver.tracks_view AS
SELECT
    value:item:id::STRING AS track_id,
    value:item:name::STRING AS track_name,
    value:item:artists[0]:name::STRING AS artist_name,
    value:item:album:name::STRING AS album_name,
    TO_TIMESTAMP_NTZ(value:timestamp::NUMBER / 1000) AS played_at,
    value:item:duration_ms::INT AS duration_ms,
    TRUE AS is_playing,
    CURRENT_TIMESTAMP() AS ingestion_timestamp
FROM spotify.raw.spotify_bronze_raw
WHERE value:item IS NOT NULL;

GRANT SELECT ON VIEW spotify.silver.tracks_view TO USER SAJY;
GRANT SELECT ON VIEW spotify.silver.tracks_view TO ROLE SYSADMIN;


-- ---------------------------------------------------------------------------
-- 4. Quick checks (run after consumer has uploaded files to S3)
-- ---------------------------------------------------------------------------

USE ROLE SYSADMIN;
USE DATABASE spotify;

LIST @spotify.raw.spotify_bronze_stage;

SELECT COUNT(*) AS raw_row_count
FROM spotify.raw.spotify_bronze_raw;

SELECT * FROM spotify.silver.tracks_view LIMIT 10;

-- Run this after new files land in S3
ALTER EXTERNAL TABLE spotify.raw.spotify_bronze_raw REFRESH;


-- ---------------------------------------------------------------------------
-- 5. After dbt run — check silver and gold
-- ---------------------------------------------------------------------------

SELECT
    (SELECT COUNT(*) FROM spotify.silver.silver_tracks) AS silver_row_count,
    (SELECT COUNT(*) FROM spotify.gold.gold_daily_summary) AS gold_row_count;

SELECT * FROM spotify.silver.silver_tracks ORDER BY played_at DESC LIMIT 10;
SELECT * FROM spotify.gold.gold_daily_summary ORDER BY date DESC LIMIT 10;
