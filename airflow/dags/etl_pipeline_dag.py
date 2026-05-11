from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

sys.path.insert(0, "/opt/airflow/etl")

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


def run_etl():
    """ETL: Postgres → MinIO (parquet, partitioned)"""
    from etl_postgres_to_minio import main as etl_main
    etl_main()


def run_data_quality():
    """Проверка качества данных"""
    from data_quality import check_nulls, check_outliers
    import pandas as pd
    from sqlalchemy import create_engine

    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DB')}"
    )

    for table in ["production", "telemetry", "deliveries"]:
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        nulls = check_nulls(df, table)
        if (nulls > 50).any():
            raise ValueError(f"Too many NULLs in {table}: {nulls.to_dict()}")

    tele = pd.read_sql("SELECT * FROM telemetry", engine)
    check_outliers(tele, ["pressure", "temperature", "power"])
    print("✅ Data Quality passed")


def build_marts():
    """Построение витрин в Postgres"""
    import pandas as pd
    from sqlalchemy import create_engine

    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DB')}"
    )

    daily = pd.read_sql("""
        SELECT prod_date,
               SUM(oil_volume) AS total_oil,
               SUM(gas_volume) AS total_gas,
               AVG(water_cut)  AS avg_water_cut
        FROM production
        GROUP BY prod_date
        ORDER BY prod_date
    """, engine)
    daily.to_sql("mart_daily_production", engine, if_exists="replace", index=False)

    kpi = pd.read_sql("""
        SELECT w.well_id, w.well_name, w.field, w.region,
               AVG(p.oil_volume) AS avg_oil,
               SUM(p.oil_volume) AS total_oil,
               AVG(t.pressure)   AS avg_pressure,
               AVG(t.temperature) AS avg_temperature,
               SUM(t.downtime)   AS total_downtime,
               SUM(t.pump_runtime) AS total_runtime
        FROM wells w
        LEFT JOIN production p ON w.well_id = p.well_id
        LEFT JOIN telemetry  t ON w.well_id = t.well_id
        GROUP BY w.well_id, w.well_name, w.field, w.region
    """, engine)
    kpi["downtime_pct"] = (
        kpi["total_downtime"] /
        (kpi["total_runtime"] + kpi["total_downtime"]) * 100
    ).round(2)
    kpi.to_sql("mart_well_kpi", engine, if_exists="replace", index=False)

    print("Marts built: mart_daily_production, mart_well_kpi")


with DAG(
    dag_id="oilfield_etl_pipeline",
    description="Daily ETL: Postgres → MinIO + DQ + Marts",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 2 * * *",
    catchup=False,
    tags=["bigdata", "etl", "oilfield"],
) as dag:

    dq_task = PythonOperator(
        task_id="data_quality_check",
        python_callable=run_data_quality,
    )

    etl_task = PythonOperator(
        task_id="etl_postgres_to_minio",
        python_callable=run_etl,
    )

    marts_task = PythonOperator(
        task_id="build_marts",
        python_callable=build_marts,
    )

    notify = BashOperator(
        task_id="notify_complete",
        bash_command='echo Pipeline completed at $(date)"',
    )

    dq_task >> etl_task >> marts_task >> notify