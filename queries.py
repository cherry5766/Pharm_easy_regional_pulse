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

# SQL evidence for memo.md and presentation_storyline.md; all derived from clean orders.
show("Guntur monthly sales, distinct orders, average order value and company share", """
WITH company AS (
 SELECT substr(order_date,1,7) month, SUM(sales_inr) company_sales
 FROM orders_clean GROUP BY 1
), regional AS (
 SELECT substr(order_date,1,7) month, SUM(sales_inr) sales,
 COUNT(DISTINCT order_id) orders FROM orders_clean WHERE region='Guntur' GROUP BY 1
)
SELECT r.month, ROUND(r.sales,2) sales_inr, r.orders,
 ROUND(r.sales/r.orders,2) average_order_value_inr,
 ROUND(100.0*r.sales/c.company_sales,2) company_sales_share_pct
FROM regional r JOIN company c USING(month) ORDER BY r.month
""")
show("Guntur April-May order count and average order value growth", """
WITH m AS (
 SELECT substr(order_date,1,7) month, SUM(sales_inr) sales,
 COUNT(DISTINCT order_id) orders FROM orders_clean WHERE region='Guntur' GROUP BY 1
)
SELECT ROUND(100.0*(b.orders-a.orders)/a.orders,2) order_growth_pct,
 ROUND(100.0*((b.sales/b.orders)-(a.sales/a.orders))/(a.sales/a.orders),2) aov_growth_pct
FROM m a JOIN m b ON a.month='2026-04' AND b.month='2026-05'
""")
show("Guntur category sales, distinct orders and contribution to April-May increase", """
WITH c AS (
 SELECT category,
 SUM(CASE WHEN substr(order_date,1,7)='2026-04' THEN sales_inr ELSE 0 END) april_sales,
 SUM(CASE WHEN substr(order_date,1,7)='2026-05' THEN sales_inr ELSE 0 END) may_sales,
 COUNT(DISTINCT CASE WHEN substr(order_date,1,7)='2026-04' THEN order_id END) april_orders,
 COUNT(DISTINCT CASE WHEN substr(order_date,1,7)='2026-05' THEN order_id END) may_orders
 FROM orders_clean WHERE region='Guntur' GROUP BY category
)
SELECT category, ROUND(april_sales,2) april_sales, ROUND(may_sales,2) may_sales,
 april_orders, may_orders, ROUND(may_sales-april_sales,2) increase_inr,
 ROUND(100.0*(may_sales-april_sales)/(SELECT SUM(may_sales-april_sales) FROM c),2) increase_share_pct
FROM c ORDER BY increase_inr DESC
""")
show("Three highlighted Guntur categories combined", """
WITH c AS (
 SELECT substr(order_date,1,7) month,
 SUM(sales_inr) total_sales,
 SUM(CASE WHEN category IN ('Wellness & Nutrition','Medical Devices','Lab Tests') THEN sales_inr ELSE 0 END) highlighted_sales,
 COUNT(DISTINCT CASE WHEN category IN ('Wellness & Nutrition','Medical Devices','Lab Tests') THEN order_id END) highlighted_orders
 FROM orders_clean WHERE region='Guntur' GROUP BY 1
)
SELECT a.highlighted_orders april_orders, b.highlighted_orders may_orders,
 ROUND(100.0*(b.highlighted_sales-a.highlighted_sales)/(b.total_sales-a.total_sales),2) combined_increase_share_pct
FROM c a JOIN c b ON a.month='2026-04' AND b.month='2026-05'
""")
show("Guntur top-five order sales concentration", """
WITH ranked AS (
 SELECT substr(order_date,1,7) month, sales_inr,
 ROW_NUMBER() OVER(PARTITION BY substr(order_date,1,7) ORDER BY sales_inr DESC,order_id) position
 FROM orders_clean WHERE region='Guntur'
)
SELECT month, ROUND(SUM(CASE WHEN position<=5 THEN sales_inr ELSE 0 END),2) top5_sales_inr,
 ROUND(100.0*SUM(CASE WHEN position<=5 THEN sales_inr ELSE 0 END)/SUM(sales_inr),2) top5_share_pct
FROM ranked GROUP BY month ORDER BY month
""")
show("Company sales including and excluding Guntur, with growth", """
WITH m AS (
 SELECT substr(order_date,1,7) month, SUM(sales_inr) sales,
 SUM(CASE WHEN region<>'Guntur' THEN sales_inr ELSE 0 END) excluding_guntur
 FROM orders_clean GROUP BY 1
)
SELECT month, ROUND(sales,2) company_sales_inr, ROUND(excluding_guntur,2) excluding_guntur_inr,
 ROUND(100.0*(sales-LAG(sales) OVER(ORDER BY month))/LAG(sales) OVER(ORDER BY month),2) company_mom_pct,
 ROUND(100.0*(excluding_guntur-LAG(excluding_guntur) OVER(ORDER BY month))/LAG(excluding_guntur) OVER(ORDER BY month),2) excluding_guntur_mom_pct
FROM m ORDER BY month
""")
show("Guntur June versus April", """
SELECT ROUND(100.0*(
 SUM(CASE WHEN substr(order_date,1,7)='2026-06' THEN sales_inr ELSE 0 END)-
 SUM(CASE WHEN substr(order_date,1,7)='2026-04' THEN sales_inr ELSE 0 END))/
 SUM(CASE WHEN substr(order_date,1,7)='2026-04' THEN sales_inr ELSE 0 END),2) june_vs_april_pct
FROM orders_clean WHERE region='Guntur'
""")
con.close()
