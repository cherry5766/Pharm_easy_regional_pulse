"""Part 1 - cleaning pipeline + schema validation."""
import json
import pandas as pd

RAW_PATH = "pharmeasy_orders_raw.csv"
CLEAN_PATH = "orders_clean.csv"
LOG_PATH = "cleaning_log.json"
REQUIRED = ["order_id", "order_date", "region", "category", "product",
            "quantity", "sales_inr", "profit_inr"]


def validate_schema(df, required_columns):
    """Return {status, rows, missing_columns}; status is 'validated' or 'blocked_schema'."""
    missing = [c for c in required_columns if c not in df.columns]
    return {
        "status": "blocked_schema" if missing else "validated",
        "rows": int(len(df)),
        "missing_columns": missing,
    }


def clean(raw_path=RAW_PATH, master_path="regions_master.csv"):
    log = {}
    df = pd.read_csv(raw_path, dtype={"order_id": str})
    log["raw_rows"] = len(df)
    log["raw_region_variants"] = int(df["region"].nunique())

    # 1. exact duplicates (all 8 columns)
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    log["duplicates_removed"] = before - len(df)
    log["rows_after_dedup"] = len(df)

    # 2. normalise region text
    df["region"] = df["region"].str.strip().str.title()
    log["canonical_regions"] = int(df["region"].nunique())
    master = pd.read_csv(master_path)
    assert set(df["region"]) <= set(master["region"]), "region outside master list"

    # 3. impute category via product -> category lookup (exact: 1 product = 1 category)
    log["missing_category_before"] = int(df["category"].isna().sum())
    known = df.dropna(subset=["category"]).drop_duplicates("product")
    lookup = dict(zip(known["product"], known["category"]))
    check = df.dropna(subset=["category"]).groupby("product")["category"].nunique()
    assert (check == 1).all(), "product maps to >1 category"
    df["category"] = df["category"].fillna(df["product"].map(lookup))
    log["missing_category_after"] = int(df["category"].isna().sum())

    # 4. impute profit with category mean margin
    log["missing_profit_before"] = int(df["profit_inr"].isna().sum())
    ok = df.dropna(subset=["profit_inr"])
    margin = (ok["profit_inr"] / ok["sales_inr"]).groupby(ok["category"]).mean()
    log["category_mean_margin"] = {k: round(float(v), 6) for k, v in margin.items()}
    miss = df["profit_inr"].isna()
    df.loc[miss, "profit_inr"] = (df.loc[miss, "sales_inr"] * df.loc[miss, "category"].map(margin)).round(2)
    log["missing_profit_after"] = int(df["profit_inr"].isna().sum())

    return df, log


if __name__ == "__main__":
    df, log = clean()
    df.to_csv(CLEAN_PATH, index=False)
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)
    print("Cleaning log:", json.dumps(log, indent=2))
    print("\nvalidate_schema (clean):  ", validate_schema(df, REQUIRED))
    broken = df.drop(columns=["profit_inr"])
    print("validate_schema (broken): ", validate_schema(broken, REQUIRED))
    print(f"\nWrote {CLEAN_PATH} ({len(df)} rows)")
