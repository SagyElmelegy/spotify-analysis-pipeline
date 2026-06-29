# Phase 5 — Power BI Dashboard

Connect Power BI Desktop to your Snowflake gold/silver models and build a Spotify listening dashboard.

> **June 2026 Power BI (2.155.756.0) bug:** The native Snowflake connector fails with  
> `Value cannot be null. Parameter name: source` even with legacy ODBC enabled.  
> **Use the CSV workaround below** (works today) or **downgrade Power BI** (fixes native connector).

## Quick fix — Import from CSV (recommended for June 2026)

1. Export data from Snowflake (run once in project folder):

   ```powershell
   cd "c:\Users\Sagy\Desktop\Study\Data Analysis\Spotify Analysis\DBT"
   docker run --rm --entrypoint python --env-file "..\.env" -v "%cd%\..\Power BI\data:/out" dbt-snowflake -c "
   import os, csv, snowflake.connector
   conn = snowflake.connector.connect(account=os.getenv('SNOWFLAKE_ACCOUNT'), user=os.getenv('SNOWFLAKE_USER'), password=os.getenv('SNOWFLAKE_PASSWORD'), database='spotify', warehouse='COMPUTE_WH')
   cur = conn.cursor()
   for name, sql in [('gold_daily_summary','SELECT * FROM spotify.gold.gold_daily_summary'), ('silver_tracks','SELECT * FROM spotify.silver.silver_tracks')]:
       cur.execute(sql); rows=cur.fetchall(); cols=[c[0] for c in cur.description]
       with open(f'/out/{name}.csv','w',newline='',encoding='utf-8') as f:
           csv.writer(f).writerows([cols]+rows)
       print(name, len(rows), 'rows')
   "
   ```

   Or: `python Scripts/export_powerbi_data.py` (requires `pip install snowflake-connector-python` in `.venv`)

2. Power BI Desktop → **Get data** → **Text/CSV**
3. Select both files in `Power BI/data/`:
   - `gold_daily_summary.csv`
   - `silver_tracks.csv`
4. Click **Load** → build visuals (same as below)
5. To refresh later, re-run the export command, then **Home → Refresh** in Power BI

---

## Prerequisites

- [Power BI Desktop](https://powerbi.microsoft.com/desktop/) installed (Windows)
- dbt models built (`cd DBT && run_dbt.bat run`)
- Snowflake credentials from project `.env`:
  - `SNOWFLAKE_ACCOUNT` — e.g. `xy12345.us-east-1` (no `https://`, no `.snowflakecomputing.com`)
  - `SNOWFLAKE_USER` — e.g. `SAJY`
  - `SNOWFLAKE_PASSWORD`
  - `SNOWFLAKE_DATABASE` — `spotify`
  - `SNOWFLAKE_WAREHOUSE` — `COMPUTE_WH`

## Step 1 — Connect to Snowflake

### Option A: Use the connection file (fastest)

1. Open `Power BI/Spotify_Analytics.pbids` in a text editor.
2. Replace `YOUR_ACCOUNT.YOUR_REGION` with your `SNOWFLAKE_ACCOUNT` value from `.env`.
   - Example: if `SNOWFLAKE_ACCOUNT=abc12345.us-east-1`, server becomes  
     `abc12345.us-east-1.snowflakecomputing.com`
3. Double-click `Spotify_Analytics.pbids` to open Power BI Desktop.
4. Sign in with **Username and password** (`SNOWFLAKE_USER` / `SNOWFLAKE_PASSWORD`).

### Option B: Manual connection

1. Power BI Desktop → **Get data** → **More…**
2. Search **Snowflake** → **Connect**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | Server | `{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com` |
   | Warehouse | `COMPUTE_WH` |
   | Database | `spotify` |
   | Data connectivity mode | **Import** (recommended for this project size) |

4. Click **OK** → **Database** → enter user and password.

## Step 2 — Load the data model

In Navigator, select these objects (check the box next to each):

| Schema | Object | Type | Use for |
|--------|--------|------|---------|
| `spotify.gold` | `gold_daily_summary` | View | Daily play counts, top tracks, charts |
| `spotify.silver` | `silver_tracks` | Table | Recent listens, timeline, detail table |

Click **Load** (or **Transform data** first if you want to rename columns in Power Query).

### Column reference

**gold_daily_summary**

| Column | Description |
|--------|-------------|
| `date` | Play date |
| `top_track` | Track name |
| `artist_name` | Artist name |
| `total_play_count` | Number of play events that day for this track |
| `avg_duration_sec` | Average track length in seconds |

**silver_tracks**

| Column | Description |
|--------|-------------|
| `track_id` | Spotify track ID |
| `track_name` | Track name |
| `artist_name` | Artist |
| `album_name` | Album |
| `played_at` | When the track was playing |
| `duration_ms` | Track length in ms |
| `ingestion_timestamp` | When the row was loaded into silver |

## Step 3 — Add DAX measures

1. **Modeling** tab → **New measure**
2. Copy measures from `Power BI/measures.dax` one at a time, or paste all into a measures table.

Recommended starter measures: `Total Plays`, `Unique Artists`, `Avg Track Length (sec)`.

## Step 4 — Build the dashboard

Create a single report page named **Spotify Listening** with these visuals:

### Row 1 — KPI cards

| Visual | Field |
|--------|-------|
| Card | `Total Plays` (measure) |
| Card | `Unique Artists` (measure) |
| Card | `Unique Tracks` (measure) |
| Card | `Avg Track Length (sec)` (measure) |

### Row 2 — Trends and ranking

| Visual | Fields |
|--------|--------|
| **Clustered bar chart** — title: *Top tracks by plays* | Y: `top_track`, X: `total_play_count`, Legend: `artist_name` |
| **Line chart** — title: *Plays over time* | X: `date`, Y: `total_play_count` |

### Row 3 — Detail

| Visual | Fields |
|--------|--------|
| **Table** — title: *Recent listens* | `played_at`, `track_name`, `artist_name`, `album_name` from `silver_tracks` |

### Slicers (right side)

- `date` (from gold)
- `artist_name` (from gold)

## Step 5 — Formatting (optional)

- Theme: **View** → **Themes** → pick a dark theme (Spotify-style)
- Sort bar chart by `total_play_count` descending
- Format `played_at` as date/time on the table visual
- Set page size: **16:9**

## Step 6 — Save and refresh

1. **File** → **Save as** → `Power BI/Spotify_Analytics.pbix`
2. To refresh after new pipeline data:
   - Ensure dbt has run (`run_dbt.bat run` or wait for Airflow DAG)
   - In Power BI Desktop: **Home** → **Refresh**

### Import vs DirectQuery

| Mode | When to use |
|------|-------------|
| **Import** (default here) | Small/medium data, fast visuals, refresh on demand |
| **DirectQuery** | Always live Snowflake data; slower visuals, warehouse cost on every interaction |

For this project, **Import** is the better default.

## Step 7 — Publish (optional)

1. **Home** → **Publish** → choose your Power BI workspace
2. In Power BI Service → dataset **Settings** → configure Snowflake credentials for scheduled refresh
3. Set refresh schedule (e.g. every hour, aligned with your Airflow DAG)

## Troubleshooting

### "Value cannot be null. Parameter name: source" (June 2026 Power BI bug)

You are on Power BI Desktop **2.155.756.0 (June 2026)** — this release has a **known Snowflake connector regression**. Snowflake data is fine; the connector fails during preview.

**Try these in order:**

#### Fix 1 — Enable legacy Snowflake connector (quickest)

1. **File** → **Options and settings** → **Options** → **Preview features**
2. Enable **Snowflake legacy ODBC version**
3. Restart Power BI Desktop
4. Connect again via **Get data → Snowflake** (do not pre-select schema in Navigator — pick **tables/views only**)

#### Fix 2 — Select objects, not whole schema

In Navigator, **do not** load the entire `gold` schema. Check only:

- `gold` → **`gold_daily_summary`** (view)
- `silver` → **`silver_tracks`** (table)

Loading a schema folder triggers the null preview error.

#### Fix 3 — Manual Power Query (bypass Navigator preview)

1. **Get data** → **Blank query** → **Advanced editor**
2. Paste the query from `Power BI/powerquery_snowflake.m` (one query per table)
3. **Done** → set credentials → repeat for `silver_tracks`

#### Fix 4 — Use ODBC instead of native Snowflake connector

1. Install [Snowflake ODBC driver](https://docs.snowflake.com/en/user-guide/odbc-download)
2. **Get data** → **ODBC**
3. DSN or connection string:

   ```
   Driver={SnowflakeDSIIDriver};Server=QOGRAXH-UQ68486.snowflakecomputing.com;Warehouse=COMPUTE_WH;Database=spotify;Schema=gold;UID=SAJY;PWD=<your_password>
   ```

4. SQL: `SELECT * FROM gold_daily_summary`

#### Fix 5 — Downgrade Power BI Desktop (fixes native Snowflake connector)

Install **February 2026** or earlier from the [Power BI archive](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-latest-update-archive). **Important:** use the **.exe** installer, **not** the Microsoft Store version (Store auto-updates back to the broken June release).

After install: disable auto-update in **File → Options → Updates**.

#### Fix 6 — ODBC connector (bypasses `Snowflake.Databases()` entirely)

1. Install [Snowflake ODBC driver 64-bit](https://docs.snowflake.com/en/user-guide/odbc-download)
2. Power BI → **Get data** → **ODBC**
3. Expand **Advanced options** → paste:

   ```
   Driver={SnowflakeDSIIDriver};Server=QOGRAXH-UQ68486.snowflakecomputing.com;Warehouse=COMPUTE_WH;Database=spotify;Schema=gold;UID=SAJY;PWD=YOUR_PASSWORD
   ```

4. Click **OK** → when prompted for SQL, use:

   ```sql
   SELECT * FROM gold_daily_summary
   ```

5. Repeat for `silver.silver_tracks` (change `Schema=silver`, SQL `SELECT * FROM silver_tracks`)

---

| Problem | Fix |
|---------|-----|
| Cannot connect to Snowflake | Verify server format: `{account}.snowflakecomputing.com` |
| Login failed | Use same user/password as `.env`; check Snowflake user is not locked |
| Empty tables | Run `run_dbt.bat run`, then refresh in Power BI |
| `gold_daily_summary` empty but bronze has data | Run `ALTER EXTERNAL TABLE spotify.raw.spotify_bronze_raw REFRESH` in Snowflake, then dbt run |
| Snowflake connector missing | Install latest Power BI Desktop; Snowflake is a built-in connector |

## Verify data in Snowflake first

```sql
SELECT COUNT(*) FROM spotify.silver.silver_tracks;
SELECT COUNT(*) FROM spotify.gold.gold_daily_summary;
SELECT * FROM spotify.gold.gold_daily_summary ORDER BY date DESC LIMIT 10;
```

Both counts should be > 0 before building the report.
