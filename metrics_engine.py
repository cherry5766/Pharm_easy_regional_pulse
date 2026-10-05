"""Part 2 - SQL metrics, MoM growth, significance flagging, state persistence."""
import json
import sqlite3

DB_PATH = "pharmeasy.db"
MONTHS = ["2026-04", "2026-05", "2026-06"]
TRANSITIONS = [("2026-04", "2026-05"), ("2026-05", "2026-06")]
STATE_PATH = "state.json"


def region_month_sales(db_path=DB_PATH):
    """{month: {region: total_sales}} straight from SQL GROUP BY."""
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT substr(order_date,1,7) AS month, region, ROUND(SUM(sales_inr),2) "
        "FROM orders_clean GROUP BY month, region ORDER BY month, region").fetchall()
    con.close()
    out = {}
    for m, r, s in rows:
        out.setdefault(m, {})[r] = s
    return out


def region_month_orders(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT substr(order_date,1,7), region, COUNT(DISTINCT order_id) "
        "FROM orders_clean GROUP BY 1, 2").fetchall()
    con.close()
    out = {}
    for m, r, n in rows:
        out.setdefault(m, {})[r] = n
    return out


def compute_percentage_change_v1(current, previous):
    """(current - previous) / previous * 100; returns 0 when previous is 0/None."""
    if not previous:
        return 0
    return (current - previous) / previous * 100


def mom_changes(prev_summary, curr_summary):
    """{region: % change} for regions present in the current month."""
    return {r: round(compute_percentage_change_v1(v, prev_summary.get(r, 0)), 2)
            for r, v in curr_summary.items()}


def flag_significant_regions_v1(changes, threshold=8):
    """Fixed-percentage operational alert (NOT a statistical test): abs(change) > threshold."""
    return [r for r, c in changes.items() if abs(c) > threshold]


def save_state_v1(month_summary, path=STATE_PATH):
    """Persist {month: {region: sales}} as JSON (merges with existing state)."""
    try:
        state = load_previous_state_v1(path)
    except FileNotFoundError:
        state = {}
    state.update(month_summary)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def load_previous_state_v1(path=STATE_PATH):
    with open(path) as f:
        return json.load(f)


def all_changes(sales):
    """{'2026-04->2026-05': {region: pct}, ...}"""
    return {f"{a}->{b}": mom_changes(sales[a], sales[b]) for a, b in TRANSITIONS}


def process_month(month, db_path=DB_PATH, state_path=STATE_PATH):
    """Query only the requested month, compare saved prior month, then persist it."""
    from datetime import datetime, timedelta
    parsed = datetime.strptime(month, "%Y-%m")
    previous_month = (parsed.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    try:
        state = load_previous_state_v1(state_path)
    except FileNotFoundError:
        state = {}
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            "SELECT region, ROUND(SUM(sales_inr),2) FROM orders_clean "
            "WHERE substr(order_date,1,7)=? GROUP BY region ORDER BY region", (month,)).fetchall()
    if not rows:
        raise ValueError(f"No orders found for {month}; state was not changed")
    current = dict(rows)
    changes = mom_changes(state[previous_month], current) if previous_month in state else None
    save_state_v1({month: current}, state_path)
    return {"month": month, "previous_month": previous_month, "sales": current,
            "changes": changes, "flagged": flag_significant_regions_v1(changes) if changes is not None else [],
            "comparison_status": "compared" if changes is not None else "baseline_saved"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compute SQL-verified regional metrics.")
    parser.add_argument("--month", help="YYYY-MM: query only this month and compare saved prior state")
    parser.add_argument("--db", "--db-path", dest="db", default=DB_PATH)
    parser.add_argument("--state", "--state-path", dest="state", default=STATE_PATH)
    args = parser.parse_args()
    if args.month:
        print(json.dumps(process_month(args.month, args.db, args.state), indent=2))
    else:
        sales = region_month_sales(args.db)
        ch = all_changes(sales)
        for k, v in ch.items():
            print(k, v)
            print("  flagged:", flag_significant_regions_v1(v))
