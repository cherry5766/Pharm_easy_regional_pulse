"""Part 2 - load clean data into SQLite (pharmeasy.db)."""
import os
import sqlite3
import pandas as pd

DB_PATH = "pharmeasy.db"


def build(db_path=DB_PATH):
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    pd.read_csv("regions_master.csv").to_sql("regions_master", con, index=False)
    pd.read_csv("orders_clean.csv", dtype={"order_id": str}).to_sql("orders_clean", con, index=False)
    con.execute("CREATE INDEX idx_orders_region ON orders_clean(region)")
    con.commit()
    for t in ("regions_master", "orders_clean"):
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n} rows")
    con.close()


if __name__ == "__main__":
    build()
