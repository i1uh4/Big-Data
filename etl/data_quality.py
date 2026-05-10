import os
import pandas as pd
from sqlalchemy import create_engine

PG_HOST = os.getenv("PG_HOST", "postgres")
PG_USER = os.getenv("PG_USER", "admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "admin")
PG_DB = os.getenv("PG_DB", "oilfield")

engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

def check_nulls(df, table):
    nulls = df.isnull().sum()
    total = len(df)
    report = (nulls / total * 100).round(2)
    print(f"\n[DQ] NULL % for {table}:")
    print(report)
    return report

def check_outliers(df, cols):
    out = {}
    for c in cols:
        if c in df.columns:
            q1, q3 = df[c].quantile([0.25, 0.75])
            iqr = q3 - q1
            mask = (df[c] < q1 - 1.5*iqr) | (df[c] > q3 + 1.5*iqr)
            out[c] = mask.sum()
    print(f"[DQ] Outliers: {out}")
    return out

if __name__ == "__main__":
    for t in ["production", "telemetry", "deliveries"]:
        df = pd.read_sql(f"SELECT * FROM {t}", engine)
        check_nulls(df, t)
    tele = pd.read_sql("SELECT * FROM telemetry", engine)
    check_outliers(tele, ["pressure", "temperature", "power"])