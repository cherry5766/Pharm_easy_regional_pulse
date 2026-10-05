"""Part 3 - Context-Insight-Implication draft generator. Every number comes from computed metrics."""
import hashlib
import json
from pathlib import Path
from metrics_engine import (region_month_sales, region_month_orders, all_changes,
                            flag_significant_regions_v1, TRANSITIONS)

MONTH_NAME = {"2026-04": "April", "2026-05": "May", "2026-06": "June"}
RUN_ID = "pending-content-fingerprint"


def _inr(x):
    return f"INR {x:,.2f}"


def draft_report_v1(flagged_regions, metrics):
    """
    flagged_regions: {"2026-04->2026-05": [regions], "2026-05->2026-06": [regions]}
    metrics: {"sales": {month: {region: sales}}, "orders": {...}, "changes": {transition: {region: pct}}}
    Returns one CII block per unique flagged region (regions flagged twice share one block).
    """
    sales, orders, changes = metrics["sales"], metrics["orders"], metrics["changes"]
    unique = sorted({r for regs in flagged_regions.values() for r in regs})
    blocks = []
    for region in unique:
        hit = [t for t, regs in flagged_regions.items() if region in regs]
        ctx, ins, imp = [], [], []
        for t in hit:
            a, b = t.split("->")
            pct = changes[t][region]
            direction = "rose" if pct > 0 else "fell"
            ctx.append(f"{region} sales {direction} from {_inr(sales[a][region])} ({orders[a][region]} orders) in "
                       f"{MONTH_NAME[a]} to {_inr(sales[b][region])} ({orders[b][region]} orders) in {MONTH_NAME[b]}.")
            ins.append(f"{MONTH_NAME[a]}->{MONTH_NAME[b]} change was {pct:+.2f}%, beyond the 8% alert threshold.")
        if len(hit) == 2:
            p1, p2 = (changes[t][region] for t in hit)
            if p1 * p2 < 0:
                imp.append("The two moves point in opposite directions, so the month-end level is a better "
                           "read than either single swing; review both months together.")
            else:
                imp.append("Both transitions moved the same way, which makes a sustained shift more plausible than a one-month blip.")
        else:
            imp.append("Single-transition flag: treat as a prompt to check order mix and order count before drawing conclusions.")
        big = max(abs(changes[t][region]) for t in hit)
        if big >= 50:
            imp.append("Swing exceeds 50%, so a regional lead should review the underlying orders this week.")
        blocks.append({
            "region": region, "run_id": RUN_ID, "transitions_flagged": hit,
            "context": " ".join(ctx), "insight": " ".join(ins), "implication": " ".join(imp),
            "status": "draft", "downstream_use_allowed": False,
        })
    return blocks


def load_metrics():
    sales = region_month_sales()
    return {"sales": sales, "orders": region_month_orders(), "changes": all_changes(sales)}


def build_drafts():
    m = load_metrics()
    flagged = {t: flag_significant_regions_v1(c) for t, c in m["changes"].items()}
    blocks = draft_report_v1(flagged, m)
    # A decision applies only to this exact data, narrative and memo snapshot.
    memo = Path("memo.md").read_text() if Path("memo.md").exists() else ""
    snapshot = {"metrics": m, "drafts": blocks, "memo": memo}
    run_id = "report-" + hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()[:20]
    for block in blocks:
        block["run_id"] = run_id
    return blocks, m, flagged


if __name__ == "__main__":
    blocks, _, flagged = build_drafts()
    print(f"{len(blocks)} unique flagged regions")
    for b in blocks:
        print(f"\n[{b['region']}] (flagged: {', '.join(b['transitions_flagged'])})")
        print(" Context:    ", b["context"])
        print(" Insight:    ", b["insight"])
        print(" Implication:", b["implication"])
    with open("draft_report.json", "w") as f:
        json.dump(blocks, f, indent=2)
