# Spotify Analytics Pipeline

End-to-end data pipeline for Spotify listening analytics.

**Flow:** Spotify API → Kafka → S3 (bronze) → Snowflake → dbt (silver/gold) → Airflow → Power BI

## Quick start

1. Copy `.env.example` to `.env` and fill in credentials
2. Run Snowflake setup: `DBT/snowflake_setup.sql`
3. Start the stack: `docker compose up -d`
4. Airflow UI: http://localhost:8080 (admin / admin)
5. Refresh Power BI data: `Power BI/refresh_data.bat`

## Project layout

| Folder | Purpose |
|--------|---------|
| `Scripts/` | Producer, consumer, OAuth, utilities |
| `Producer/`, `Consumer/` | Docker images for ingestion |
| `DBT/` | dbt models and tests |
| `Airflow/` | DAG that runs dbt every 15 minutes |
| `Power BI/` | Dashboard assets and refresh script |
