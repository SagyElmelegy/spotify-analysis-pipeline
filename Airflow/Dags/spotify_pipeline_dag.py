# Airflow DAG: refresh bronze in Snowflake, run dbt, then run dbt tests.
# Runs every 15 minutes when the DAG is unpaused in the Airflow UI.

from datetime import datetime, timedelta

from airflow import DAG

try:
    from airflow.providers.standard.operators.bash import BashOperator
except ImportError:
    from airflow.operators.bash import BashOperator

default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dbt_folder = "cd /opt/airflow/dbt && dbt"

with DAG(
    dag_id="spotify_analytics_pipeline",
    default_args=default_args,
    description="Refresh Snowflake bronze, run dbt models, run dbt tests",
    schedule_interval="*/15 * * * *",
    catchup=False,
    tags=["spotify", "analytics", "dbt"],
) as dag:

    refresh_bronze = BashOperator(
        task_id="refresh_snowflake_bronze",
        bash_command="python /opt/airflow/scripts/refresh_bronze.py",
    )

    run_dbt = BashOperator(
        task_id="run_dbt_transformations",
        bash_command=f"{dbt_folder} run --profiles-dir .",
    )

    test_dbt = BashOperator(
        task_id="test_dbt_quality",
        bash_command=f"{dbt_folder} test --profiles-dir .",
    )

    refresh_bronze >> run_dbt >> test_dbt
