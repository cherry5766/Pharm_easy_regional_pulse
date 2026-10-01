# Data-Quality Report

Source: `pharmeasy_orders_raw.csv` (2,159 rows) → `orders_clean.csv` (2,100 rows). Counts below are written to `cleaning_log.json` on every run of `clean_data.py`.

## Fixes mapped to data-quality dimensions

| Step | Problem found | Fix | Dimension |
|---|---|---|---|
| 1 | 59 rows identical across all 8 columns (copy-paste from multiple source sheets) | `drop_duplicates()`, 2,159 → 2,100 | **Uniqueness**, and **Accuracy** (duplicates inflate sales and order counts) |
| 2 | 16 raw region strings (stray spaces, mixed case) for what are 9 active regions | `strip()` + `title()` → exactly 9 canonical names matching `regions_master.csv` | **Consistency**, and **Validity** (values conform to the master list) |
| 3 | 48 missing `category` values | Product → category lookup built from non-missing rows (each product maps to exactly one category; asserted in code) | **Completeness** |
| 4 | 94 missing `profit_inr` values (nightly sync gaps) | `sales_inr × category mean margin`, rounded to 2 decimals | **Completeness** (an estimate, so Accuracy of these cells is approximate) |
| 5 | Region/month metrics must reflect only real, in-scope regions | `regions_master` LEFT JOIN check keeps zero-order Kurnool visible instead of silently dropping it | **Relevance** and **Completeness** of the region list |

## All seven dimensions

- **Accuracy:** removing duplicates prevents double-counted sales; imputed profit is flagged as an estimate (category margins range 14.79%–15.28%).
- **Completeness:** zero missing `category` and zero missing `profit_inr` remain after imputation (verified in `cleaning_log.json`).
- **Consistency:** one canonical spelling per region.
- **Timeliness:** all `order_date` values fall within April–June 2026 and aggregate by `YYYY-MM`; the saved JSON state lets a later month be added without recomputing history. No stale or out-of-period rows were found, so no rows were removed for this dimension.
- **Validity:** regions checked against `regions_master.csv`; `validate_schema()` blocks the pipeline if a required column is missing.
- **Uniqueness:** `order_id` is unique after de-duplication (verified by the GROUP BY ... HAVING check in `queries.py`).
- **Relevance:** only the 8 fields needed for regional performance are carried; no personal customer data is present or used.

## Schema validation demonstration
`clean_data.py` prints `validated` for the clean data and `blocked_schema` with `missing_columns: ['profit_inr']` for a copy with that column dropped.
