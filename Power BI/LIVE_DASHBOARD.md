# Live dashboard setup for spotify.pbix

Your pipeline cannot push **second-by-second** updates into a local `.pbix` file automatically.
The practical setup is **near real-time (~15 minutes)** using the pipeline + refresh.

## Architecture

```
Spotify -> Producer -> Kafka -> Consumer -> S3 -> Snowflake bronze
                                              -> Airflow (every 15 min): refresh bronze + dbt
                                              -> Power BI: refresh CSV or Snowflake
```

## Step 1 — Save spotify.pbix in the project

Save your report as:

`Power BI/spotify.pbix`

This keeps it next to the CSV data folder.

## Step 2 — Connect spotify.pbix to the data folder (recommended)

If your report still uses static CSV paths, point it at the project folder so refresh picks up new files.

1. **Transform data** (Home -> Transform data)
2. For each query (`gold_daily_summary`, `silver_tracks`):
   - **Source** should be:
     `...\Spotify Analysis\Power BI\data\gold_daily_summary.csv`
     `...\Spotify Analysis\Power BI\data\silver_tracks.csv`
3. **Close & Apply**

Column names from export are **UPPERCASE** (`DATE`, `TOP_TRACK`, `TOTAL_PLAY_COUNT`, etc.).
Use the updated measures in `Power BI/measures.dax`.

## Step 3 — Refresh data from the pipeline

With Docker running (producer + consumer + Airflow):

```powershell
cd "c:\Users\Sagy\Desktop\Study\Data Analysis\Spotify Analysis\Power BI"
.\refresh_data.bat
```

This will:

1. Refresh Snowflake bronze external table
2. Run dbt (`silver_tracks`, `gold_daily_summary`)
3. Export fresh CSVs to `Power BI/data/`

Then in Power BI Desktop: **Home -> Refresh**.

## Step 4 — Keep the pipeline running

```powershell
cd "c:\Users\Sagy\Desktop\Study\Data Analysis\Spotify Analysis"
docker compose up -d
```

- **Airflow** (http://localhost:8080): unpause `spotify_analytics_pipeline` — runs dbt every 15 min
- **Producer/consumer**: new Spotify plays -> S3 -> Snowflake

## Step 5 — Automate refresh (optional, local)

**Task Scheduler** (every 15 minutes):

1. Open **Task Scheduler** -> Create Basic Task
2. Trigger: Daily, repeat every **15 minutes** for 24 hours
3. Action: Start a program
   - Program: `Power BI\refresh_data.bat`
   - Start in: `c:\Users\Sagy\Desktop\Study\Data Analysis\Spotify Analysis\Power BI`

Workflow: script updates CSVs -> you click **Refresh** in Power BI (Desktop does not auto-refresh Import mode without Power BI Service).

## Step 6 — Fully automatic refresh (Power BI Service)

1. Fix Snowflake connector (downgrade Power BI) or use ODBC
2. Connect `spotify.pbix` directly to Snowflake tables (Import mode)
3. **Publish** to Power BI Service
4. Dataset settings -> **Scheduled refresh** every 15 minutes
5. Keep Airflow + pipeline running

This is the only way to refresh **without** opening Desktop.

## Verify data is fresh

After `refresh_data.bat`:

```powershell
Get-Content "Power BI\data\gold_daily_summary.csv" -TotalCount 3
```

Check dates include today. In Power BI, add a **Card** with measure **Last Refreshed** from `measures.dax`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Refresh shows old songs | Run `refresh_data.bat`, then Home -> Refresh |
| Measures error on column names | Use UPPERCASE names in DAX (see measures.dax) |
| Empty gold table | Pipeline stopped — `docker compose up -d`, play Spotify, wait 15 min |
| dbt fails in refresh_data.bat | Check `.env` Snowflake credentials |
