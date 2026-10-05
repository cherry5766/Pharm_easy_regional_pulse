"""Part 2 - load clean data into SQLite (pharmeasy.db)."""
import os
import sqlite3
import pandas as pd
from clean_data import validate_schema, REQUIRED

DB_PATH = "pharmeasy.db"


def build(db_path=DB_PATH):
    master = pd.read_csv("regions_master.csv")
    orders = pd.read_csv("orders_clean.csv", dtype={"order_id": str})
    for data, columns in [(master, ["region", "state", "tier"]), (orders, REQUIRED)]:
        result = validate_schema(data, columns)
        if result["status"] != "validated":
            raise ValueError(f"blocked_schema: {result['missing_columns']}")
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    master.to_sql("regions_master", con, index=False)
    orders.to_sql("orders_clean", con, index=False)
    con.execute("CREATE INDEX idx_orders_region ON orders_clean(region)")
    con.commit()
    for t in ("regions_master", "orders_clean"):
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n} rows")
    con.close()


if __name__ == "__main__":
    build()
