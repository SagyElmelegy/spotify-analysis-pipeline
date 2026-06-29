@echo off
REM Updates Snowflake + CSV files for the Power BI report.
REM Run from: Power BI\refresh_data.bat

setlocal
cd /d "%~dp0.."

echo Step 1: Refresh Snowflake bronze table...
docker run --rm --entrypoint python --env-file ".env" -v "%cd%\Scripts:/scripts" dbt-snowflake /scripts/refresh_bronze.py
if errorlevel 1 echo Warning: bronze refresh failed, continuing anyway...

echo.
echo Step 2: Run dbt...
cd DBT
call run_dbt.bat run
if errorlevel 1 exit /b 1

echo.
echo Step 3: Export CSV files for Power BI...
docker run --rm --entrypoint python --env-file "..\.env" -v "%cd%\..\Power BI\data:/out" -v "%cd%\..\Scripts:/scripts" dbt-snowflake /scripts/export_powerbi_docker.py
if errorlevel 1 exit /b 1

echo.
echo Done. Open spotify.pbix and click Home ^> Refresh.
endlocal
