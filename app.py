"""Part 4 - PharmEasy Regional Pulse dashboard.  Run:  streamlit run app.py
Runs fully offline: reads pharmeasy.db, draft_report.py output and audit_log.jsonl."""
import os
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from draft_report import build_drafts
from metrics_engine import TRANSITIONS, compute_percentage_change_v1, flag_significant_regions_v1
from review_gate import load_latest_decisions, review_gate_v1

st.set_page_config(page_title="PharmEasy Regional Pulse", layout="wide")

BASE, HIGHLIGHT = "#9AA8B8", "#E4572E"          # highlight colour = selected / flagged region only
BLUES = ["#08306B", "#2171B5", "#4292C6", "#6BAED6", "#9ECAE1", "#C6DBEF"]  # one hue for part-of-whole
MONTH_LABEL = {"2026-04": "Apr 2026", "2026-05": "May 2026", "2026-06": "Jun 2026"}

if not os.path.exists("pharmeasy.db"):
    st.error("pharmeasy.db not found. Run `python3 run_pipeline.py` first.")
    st.stop()


@st.cache_data
def load():
    con = sqlite3.connect("pharmeasy.db")
    orders = pd.read_sql_query("SELECT *, substr(order_date,1,7) AS month FROM orders_clean", con)
    master = pd.read_sql_query("SELECT * FROM regions_master", con)
    con.close()
    return orders, master


orders, master = load()
drafts, metrics, flagged = build_drafts()
changes = metrics["changes"]
run_id = drafts[0]["run_id"]
decisions = load_latest_decisions(run_id)
mode = st.sidebar.radio("View", ["Reviewer workspace", "Approved stakeholder dashboard"])
st.sidebar.caption("Reviews apply to the current data, narrative and memo version.")
reviewer_name = st.sidebar.text_input("Reviewer name", key="reviewer_name")
unapproved = [d["region"] for d in drafts if decisions.get(d["region"], {}).get("decision") != "approve"]
if mode == "Approved stakeholder dashboard" and unapproved:
    st.title("PharmEasy Regional Pulse")
    st.warning("Stakeholder dashboard is locked until all flagged-region reports and the Guntur memo have been approved for this version.")
    st.write("Awaiting approval: " + ", ".join(unapproved))
    st.stop()
if mode == "Reviewer workspace":
    st.warning("Reviewer workspace: the numbers and narratives below are drafts for human validation. They are not cleared for stakeholder use.")

# ------------------------------------------------------------------ executive summary
total_sales, total_profit = orders.sales_inr.sum(), orders.profit_inr.sum()
n_orders = orders.order_id.nunique()
monthly = orders.groupby("month").sales_inr.sum()
cat_share = orders.groupby("category").sales_inr.sum().sort_values(ascending=False)
reg_share = orders.groupby("region").sales_inr.sum().sort_values(ascending=False)
big_t, big_r, big_v = max(((t, r, v) for t, c in changes.items() for r, v in c.items()), key=lambda x: abs(x[2]))
a, b = big_t.split("->")
n_flag = len(flagged[big_t])
n_regions = orders.region.nunique()

st.title("PharmEasy Regional Pulse")
st.caption("Telugu-states regional desk (plus Bengaluru hub) · April–June 2026 · cleaned, SQL-verified data")
summary = (
    f"Across April-June 2026 the desk booked INR {total_sales:,.0f} in sales and INR {total_profit:,.0f} in profit "
    f"from {n_orders:,} distinct orders. "
    f"Monthly sales were steady (INR {monthly.min():,.0f} to INR {monthly.max():,.0f}), but regions moved sharply underneath that stability. "
    f"{cat_share.index[0]} is the largest category at {cat_share.iloc[0] / total_sales:.1%} of sales and {reg_share.index[0]} the largest region at "
    f"{reg_share.iloc[0] / total_sales:.1%}. "
    f"The biggest swing is {big_r}'s {MONTH_LABEL[a][:3]}->{MONTH_LABEL[b][:3]} change of {big_v:+.2f}%, which a regional lead should review before any target or stock decision "
    f"(note {n_flag} of {n_regions} regions crossed the 8% alert that month, so flags are prompts, not proof). "
    f"Use the region filter below to move from category mix to the region-by-month detail."
)
st.info(summary)

# ------------------------------------------------------------------ region filter (connects all levels)
options = ["All regions"] + master.region.tolist()
sel = st.selectbox("Region filter (updates KPIs, category view, detail table and narrative)", options)
view = orders if sel == "All regions" else orders[orders.region == sel]

# ------------------------------------------------------------------ level 1: overview
st.header("1 · Overview")
k1, k2, k3 = st.columns(3)
k1.metric("Total sales (INR)", f"{view.sales_inr.sum():,.2f}")
k2.metric("Total profit (INR)", f"{view.profit_inr.sum():,.2f}")
k3.metric("Orders (distinct order_id)", f"{view.order_id.nunique():,}")
if sel == "Kurnool":
    st.warning("Kurnool is in the regions master but has zero orders in this export (kept visible by design).")

# trend chart: monthly sales by region
reg_month = orders.groupby(["region", "month"]).sales_inr.sum().reset_index()
fig_line = go.Figure()
for r in sorted(reg_month.region.unique()):
    d = reg_month[reg_month.region == r].sort_values("month")
    hit = r == sel and any(r in regions for regions in flagged.values())
    fig_line.add_trace(go.Scatter(
        x=[MONTH_LABEL[m] for m in d.month], y=d.sales_inr, mode="lines+markers", name=r,
        line=dict(color=HIGHLIGHT if hit else BASE, width=4 if hit else 1.5),
        opacity=1 if (hit or sel == "All regions") else 0.6))
fig_line.update_layout(title="How did monthly sales change in each region from April to June?",
                       xaxis_title="Month (2026)", yaxis_title="Sales (INR)", height=420,
                       legend_title="Region", margin=dict(t=60))
fig_line.update_yaxes(rangemode="tozero", tickformat=",")
st.plotly_chart(fig_line, width="stretch")

# bar chart: total sales by region
tot = orders.groupby("region").sales_inr.sum().reindex(master.region).fillna(0).sort_values(ascending=False)
fig_bar = go.Figure(go.Bar(x=tot.index, y=tot.values,
                           marker_color=[HIGHLIGHT if r == sel and any(r in regions for regions in flagged.values()) else BASE for r in tot.index]))
fig_bar.update_layout(title="Which regions generate the most sales (Apr-Jun 2026)?",
                      xaxis_title="Region", yaxis_title="Total sales (INR)", height=400, margin=dict(t=60))
fig_bar.update_yaxes(rangemode="tozero", tickformat=",")
st.plotly_chart(fig_bar, width="stretch")

# ------------------------------------------------------------------ level 2: category
st.header(f"2 · Category breakdown ({sel})")
if view.empty:
    st.info("No orders for this selection.")
else:
    cat = view.groupby("category").sales_inr.sum().sort_values(ascending=False)
    c1, c2 = st.columns(2)
    fig_cat = go.Figure(go.Bar(x=cat.values, y=cat.index, orientation="h", marker_color=BASE))
    fig_cat.update_layout(title="Which categories drive sales here?", xaxis_title="Sales (INR)",
                          yaxis_title="Category", yaxis=dict(autorange="reversed"), height=400, margin=dict(t=60))
    fig_cat.update_xaxes(rangemode="tozero", tickformat=",")
    c1.plotly_chart(fig_cat, width="stretch")
    fig_pie = go.Figure(go.Pie(labels=cat.index, values=cat.values, hole=0.5, sort=False,
                               marker=dict(colors=BLUES[:len(cat)]), textinfo="percent"))
    fig_pie.update_layout(title="What share of sales does each category contribute?", height=400, margin=dict(t=60))
    c2.plotly_chart(fig_pie, width="stretch")

# ------------------------------------------------------------------ level 3: detail
st.header(f"3 · Region × month detail ({sel})")
grid = pd.MultiIndex.from_product([master.region, sorted(MONTH_LABEL)], names=["region", "month"]).to_frame(index=False)
agg = orders.groupby(["region", "month"]).agg(orders=("order_id", "nunique"), sales_inr=("sales_inr", "sum"),
                                              profit_inr=("profit_inr", "sum")).reset_index()
detail = grid.merge(agg, how="left", on=["region", "month"]).fillna({"orders": 0, "sales_inr": 0, "profit_inr": 0})
detail["mom_pct"] = None
detail["flagged"] = ""
for t, c in changes.items():
    _, cur = t.split("->")
    for r in c:
        m = (detail.region == r) & (detail.month == cur)
        detail.loc[m, "mom_pct"] = c[r]
        detail.loc[m, "flagged"] = "⚑ >8%" if r in flagged[t] else ""
detail["month"] = detail.month.map(MONTH_LABEL)
detail["orders"] = detail.orders.astype(int)
if sel != "All regions":
    detail = detail[detail.region == sel]
st.dataframe(detail.rename(columns={"sales_inr": "Sales (INR)", "profit_inr": "Profit (INR)", "orders": "Orders",
                                    "mom_pct": "MoM sales change (%)", "flagged": "Alert"}),
             width="stretch", hide_index=True)
st.caption("Alert = fixed 8% operational rule, not a statistical test. Profit includes 94 imputed values (category mean margin).")

# ------------------------------------------------------------------ narrative with human review gate
st.header("Insight Narrative (Context - Insight - Implication)")
st.caption("Generated live by draft_report_v1() from this session's own SQL-verified metrics. Nothing below is approved "
           "automatically - each block waits for a human reviewer to Approve, Edit, or Reject it before that decision is logged to audit_log.jsonl.")

STATUS = {"approve": "✅ approved", "edit": "✏️ needs edit", "reject": "🚫 rejected", None: "awaiting human review"}
flagship = big_r  # largest-magnitude flagged swing gets the star
for d in drafts:
    reg = d["region"]
    dec = decisions.get(reg)
    state = dec["decision"] if dec else None
    star = "⭐ " if reg == flagship else ""
    trans = ", ".join(x.replace("->", "_") for x in d["transitions_flagged"])
    label = f"{star}{reg} (flagged in: {trans}) — {STATUS[state]}"
    with st.expander(label, expanded=(reg == sel) or (sel == "All regions" and reg == flagship)):
        st.markdown(f"**Context.** {d['context']}")
        st.markdown(f"**Insight.** {d['insight']}")
        st.markdown(f"**Implication.** {d['implication']}")
        if reg == "Guntur":
            from pathlib import Path
            st.markdown("**Recommendation memo (included in this approval)**")
            st.markdown(Path("memo.md").read_text())
        if mode == "Approved stakeholder dashboard":
            st.caption("Approved for this data, narrative and memo version.")
            continue
        st.divider()
        st.markdown("**Human review gate** — this block is not shown as reviewed until you decide:")
        note = st.text_area("Reviewer note (optional but recommended)", key=f"note_{reg}", height=90,
                            placeholder="e.g. Numbers checked against Part 2 SQL output; ready for the regional lead.")
        memo_reviewed = st.checkbox("I reviewed the Guntur recommendation memo above.", key="memo_reviewed") if reg == "Guntur" else True
        b1, b2, b3 = st.columns(3)
        clicked = None
        if b1.button("Approve", key=f"approve_{reg}", icon="✅"):
            clicked = "approve"
        if b2.button("Edit", key=f"edit_{reg}", icon="✏️"):
            clicked = "edit"
        if b3.button("Reject", key=f"reject_{reg}", icon="🚫"):
            clicked = "reject"
        if clicked:
            if clicked == "approve" and not memo_reviewed:
                st.error("Review the Guntur memo and check its acknowledgement before approving.")
            elif not reviewer_name.strip() or not note.strip():
                st.error("Enter your reviewer name in the sidebar and a review note before recording a decision.")
            else:
                review_gate_v1(d, clicked, f"Reviewer: {reviewer_name.strip()} | {note.strip()}" + (" | Guntur memo reviewed" if reg == "Guntur" and memo_reviewed else ""))
                st.session_state[f"flash_{reg}"] = f"Recorded: {clicked} for {reg}."
                st.rerun()
        if st.session_state.get(f"flash_{reg}"):
            st.success(st.session_state.pop(f"flash_{reg}"))
        if dec:
            st.caption(f"Latest decision: {dec['decision']} at {dec['timestamp']}"
                       + (f" — note: {dec['reviewer_note']}" if dec["reviewer_note"] else ""))
