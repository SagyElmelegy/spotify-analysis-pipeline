@echo off
REM Run dbt inside Docker. Example: run_dbt.bat run
cd /d "%~dp0"
docker build -t dbt-snowflake .
docker run --rm --user 50000:0 --env-file "..\.env" -v "%cd%":/app -w /app dbt-snowflake %*
