"""Part 2 - JOIN validation + metrics SQL, with printed output."""
import sqlite3
import pandas as pd

con = sqlite3.connect("pharmeasy.db")


def show(title, sql):
    print(f"\n=== {title} ===\n{sql.strip()}")
    df = pd.read_sql_query(sql, con)
    print(df.to_string(index=False) if len(df) else "(zero rows)")
    return df


# 2.2 JOIN validation
left = show("Row count: LEFT JOIN",
            "SELECT COUNT(*) AS n FROM regions_master r LEFT JOIN orders_clean o ON r.region = o.region")
inner = show("Row count: INNER JOIN",
             "SELECT COUNT(*) AS n FROM regions_master r INNER JOIN orders_clean o ON r.region = o.region")
print(f"\nDelta LEFT - INNER = {left.n[0] - inner.n[0]} (Kurnool's null-padded row)")

show("Duplicate-key check (expect zero rows)",
     "SELECT order_id, COUNT(*) AS c FROM orders_clean GROUP BY order_id HAVING COUNT(*) > 1")

cmp_df = show("COUNT(*) vs COUNT(o.order_id) per region",
              """SELECT r.region, COUNT(*) AS count_star, COUNT(o.order_id) AS count_order_id,
                        CASE WHEN COUNT(*) <> COUNT(o.order_id) THEN 'DISAGREE' ELSE '' END AS note
                 FROM regions_master r LEFT JOIN orders_clean o ON r.region = o.region
                 GROUP BY r.region ORDER BY r.region""")
k = cmp_df[cmp_df.region == "Kurnool"].iloc[0]
print(f"\nKurnool: COUNT(*) = {k.count_star} (WRONG, counts null-padded row) vs COUNT(order_id) = {k.count_order_id} (correct)")

show("Per-region order counts (LEFT JOIN + GROUP BY, ascending)",
     """SELECT r.region, COUNT(o.order_id) AS orders
        FROM regions_master r LEFT JOIN orders_clean o ON r.region = o.region
        GROUP BY r.region ORDER BY orders ASC, r.region""")

# 2.3 Region x month sales and MoM growth
sales = show("Total sales per region per month",
             """SELECT region, substr(order_date,1,7) AS month, ROUND(SUM(sales_inr),2) AS sales_inr
                FROM orders_clean GROUP BY region, month ORDER BY region, month""")

show("MoM growth % (SQL, window function LAG)",
     """SELECT region, month, sales_inr,
               ROUND((sales_inr - LAG(sales_inr) OVER (PARTITION BY region ORDER BY month))
                     / LAG(sales_inr) OVER (PARTITION BY region ORDER BY month) * 100, 2) AS mom_pct
        FROM (SELECT region, substr(order_date,1,7) AS month, ROUND(SUM(sales_inr),2) AS sales_inr
              FROM orders_clean GROUP BY region, month)
        ORDER BY region, month""")

from metrics_engine import (region_month_sales, all_changes, flag_significant_regions_v1,
                            save_state_v1, load_previous_state_v1)
s = region_month_sales()
print("\n=== Significance flags (threshold = 8%) ===")
for k_, v in all_changes(s).items():
    print(k_, "flagged:", flag_significant_regions_v1(v), "| not flagged:",
          [r for r in v if r not in flag_significant_regions_v1(v)])

# 2.4 state persistence round trip
save_state_v1({"2026-04": s["2026-04"]}, "state_april.json")
assert load_previous_state_v1("state_april.json") == {"2026-04": s["2026-04"]}
save_state_v1(s, "state.json")
print("\nState round-trip OK (state_april.json, state.json written)")
