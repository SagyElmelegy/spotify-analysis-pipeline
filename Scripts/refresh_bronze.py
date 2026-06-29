# Tell Snowflake to pick up new files from S3 into the bronze external table.

import os

import snowflake.connector


def main():
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE", "spotify"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    )
    cursor = conn.cursor()
    cursor.execute("ALTER EXTERNAL TABLE spotify.raw.spotify_bronze_raw REFRESH")
    print("Bronze external table refreshed")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
