# Export Snowflake tables to CSV — used by Power BI/refresh_data.bat inside Docker.

import csv
import os
from pathlib import Path

import snowflake.connector

output_folder = Path(os.getenv("PBI_OUTPUT_DIR", "/out"))

queries = [
    ("gold_daily_summary", "SELECT * FROM spotify.gold.gold_daily_summary"),
    ("silver_tracks", "SELECT * FROM spotify.silver.silver_tracks"),
]


def main():
    output_folder.mkdir(parents=True, exist_ok=True)

    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE", "spotify"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    )
    cursor = conn.cursor()

    for file_name, sql in queries:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        csv_path = output_folder / f"{file_name}.csv"

        with csv_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)

        print(f"{file_name}: {len(rows)} rows -> {csv_path}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
