import os
import io
import pandas as pd
from sqlalchemy import create_engine
from minio import Minio

PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "admin")
PG_DB = os.getenv("PG_DB", "oilfield")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:2900")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

BUCKET_RAW = "raw"
BUCKET_PROCESSED = "processed"

engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")
client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)

def ensure_bucket(name):
    if not client.bucket_exists(name):
        client.make_bucket(name)
        print(f"Bucket {name} created")

def upload_df(df, bucket, key):
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)
    client.put_object(bucket, key, buf, length=buf.getbuffer().nbytes,
                      content_type="application/octet-stream")
    print(f"Uploaded {bucket}/{key} ({len(df)} rows)")

def extract_table(table):
    return pd.read_sql(f"SELECT * FROM {table}", engine)

def partition_by_date(df, date_col, bucket, table_name):
    """Сохраняем партиционировано по дате"""
    df[date_col] = pd.to_datetime(df[date_col])
    df['_date'] = df[date_col].dt.date
    for d, group in df.groupby('_date'):
        key = f"{table_name}/date={d}/data.parquet"
        upload_df(group.drop(columns=['_date']), bucket, key)

def main():
    for b in [BUCKET_RAW, BUCKET_PROCESSED, "marts"]:
        ensure_bucket(b)

    # 1. Извлечение и сохранение в raw
    tables = {
        "wells": None,
        "production": "prod_date",
        "telemetry": "ts",
        "well_targets": "target_date",
        "pump_sensors": "ts",
        "pump_failures": "fail_ts",
        "deliveries": "delivery_date",
    }

    for table, date_col in tables.items():
        df = extract_table(table)
        print(f"Extracted {table}: {len(df)} rows")
        if date_col and len(df) > 0:
            partition_by_date(df, date_col, BUCKET_RAW, table)
        else:
            upload_df(df, BUCKET_RAW, f"{table}/data.parquet")

    # 2. Очистка и обработка
    tele = extract_table("telemetry")
    prod = extract_table("production")

    # Обработка NULL
    tele = tele.dropna(subset=["pressure", "temperature"])
    # Фильтр выбросов IQR
    for col in ["pressure", "temperature", "power"]:
        q1, q3 = tele[col].quantile([0.05, 0.95])
        tele = tele[(tele[col] >= q1) & (tele[col] <= q3)]

    tele["ts"] = pd.to_datetime(tele["ts"])
    tele["date"] = tele["ts"].dt.date

    # Агрегация по дням и скважинам
    daily = tele.groupby(["well_id", "date"]).agg(
        avg_pressure=("pressure", "mean"),
        avg_temperature=("temperature", "mean"),
        avg_power=("power", "mean"),
        total_runtime=("pump_runtime", "sum"),
        total_downtime=("downtime", "sum"),
    ).reset_index()
    daily["downtime_ratio"] = daily["total_downtime"] / (daily["total_runtime"] + daily["total_downtime"] + 1e-6)

    # Витрина: mart_production
    prod["prod_date"] = pd.to_datetime(prod["prod_date"]).dt.date
    daily["date"] = pd.to_datetime(daily["date"]).dt.date
    mart = prod.merge(daily, left_on=["well_id", "prod_date"], right_on=["well_id", "date"], how="left")
    upload_df(mart, "marts", "mart_production/data.parquet")
    upload_df(daily, BUCKET_PROCESSED, "telemetry_daily/data.parquet")

    print("ETL completed")

if __name__ == "__main__":
    main()