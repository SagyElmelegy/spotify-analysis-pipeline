# Spotify Analytics Pipeline

An end-to-end data engineering project that turns your Spotify listening history into a live Power BI dashboard. The pipeline ingests recently played tracks, stores them in the cloud, transforms them with dbt, and refreshes on a schedule so the dashboard stays up to date.

## Architecture

```
Spotify API  →  Kafka  →  S3 (bronze)  →  Snowflake  →  dbt (silver / gold)  →  Airflow  →  Power BI
```

| Layer | What it does |
|-------|----------------|
| **Ingestion** | A producer polls the Spotify API and publishes events to Kafka; a consumer writes raw JSON to S3. |
| **Storage** | Snowflake reads bronze data from S3 via an external table. |
| **Transform** | dbt builds cleaned `silver` models and aggregated `gold` summaries with tests. |
| **Orchestration** | Airflow runs bronze refresh, `dbt run`, and `dbt test` every 15 minutes. |
| **Visualization** | Power BI connects to the gold layer (or exported CSV) for the dashboard below. |

## Final product — Spotify Listening Dashboard

The end result is a two-page Power BI report built on the gold summary data.

### Your Listening In a Glance

Overview KPIs (unique tracks, listening hours, artists, total plays), a date filter, and a bar chart of your most-played tracks.

![Your Listening In a Glance](Visualizations/Your%20listening%20in%20a%20glance%20.png)

### Who & What You Love

Artist share by play count, a distribution of how often top tracks are played, and slicers to filter by date and artist.

![Who & What You Love](Visualizations/Who%20%26%20What%20you%20love%20.png)

## Quick start

1. Copy `.env.example` to `.env` and fill in Spotify, AWS, and Snowflake credentials.
2. Run the Snowflake setup script: `DBT/snowflake_setup.sql`
3. Configure dbt: copy `DBT/profiles.example.yml` to `DBT/profiles.yml` (not committed).
4. Start the stack: `docker compose up -d`
5. Open Airflow: http://localhost:8080 (default: `admin` / `admin`)
6. Refresh Power BI data: run `Power BI/refresh_data.bat`, then open the `.pbix` report locally.

## Project layout

| Folder | Purpose |
|--------|---------|
| `Scripts/` | Spotify producer/consumer, OAuth helper, S3 and export utilities |
| `Producer/`, `Consumer/` | Docker images for Kafka ingestion |
| `DBT/` | dbt models, tests, and Snowflake setup |
| `Airflow/` | DAG that orchestrates the pipeline |
| `Power BI/` | Dashboard assets, DAX measures, and data refresh script |
| `Visualizations/` | Screenshots of the finished dashboard |
