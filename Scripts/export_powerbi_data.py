# Export Snowflake tables to CSV for Power BI (run on your machine, not in Docker).
# Needs: pip install snowflake-connector-python python-dotenv

import csv
import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_file)

output_folder = Path(__file__).resolve().parent.parent / "Power BI" / "data"
output_folder.mkdir(parents=True, exist_ok=True)

queries = [
    ("gold_daily_summary", "SELECT * FROM spotify.gold.gold_daily_summary"),
    ("silver_tracks", "SELECT * FROM spotify.silver.silver_tracks"),
]


def main():
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

        print(f"Wrote {len(rows)} rows -> {csv_path}")

    cursor.close()
    conn.close()
    print("\nNext: open Power BI and refresh your report.")


if __name__ == "__main__":
    main()
