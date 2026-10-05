# PharmEasy Regional Pulse

A single, repeatable pipeline: raw monthly order export → cleaning → SQLite-verified metrics → significance flags → draft narrative → human review gate with audit log → interactive dashboard. No API keys, no paid services, no network access needed.

## 1. Install and run (three commands from a fresh clone)

```bash
pip install -r requirements.txt
python3 run_pipeline.py        # generate -> clean -> SQLite -> queries -> drafts (nothing is auto-approved)
streamlit run app.py           # dashboard at http://localhost:8501
```

`run_pipeline.py` runs these stages in order (each can also be run on its own):

| Stage | Command | Produces |
|---|---|---|
| Dataset | `python3 generate_dataset.py` | `pharmeasy_orders_raw.csv` (2,159 rows), `regions_master.csv` (10 regions) |
| Cleaning + schema check | `python3 clean_data.py` | `orders_clean.csv` (2,100 rows), `cleaning_log.json` |
| Database | `python3 build_db.py` | `pharmeasy.db` (`regions_master`, `orders_clean`) |
| SQL validation + metrics | `python3 queries.py` | JOIN checks, region × month sales, MoM, flags, `state.json` |
| Draft report | `python3 draft_report.py` | CII block per flagged region (`draft_report.json`) |
| Review gate (test) | `python3 review_gate.py` | harness over approve / edit / reject; entries tagged `run_id=test-harness` |
| Review gate (real) | `python3 review_gate.py --review` | a human approves / edits / rejects each draft; logged to `audit_log.jsonl` |

**Human review is never automatic.** Open the dashboard in **Reviewer** mode to inspect the current data and drafts. For each region, enter a reviewer name and substantive note, then choose Approve / Edit / Reject. The **Stakeholder** view remains blocked until all eight current drafts have approval. Edit and reject do not permit downstream use; an edited draft needs another review.

Approvals are tied to the current content hash, so changing the data or generated report invalidates previous approvals. Test-harness entries are excluded from real decisions. The audit log is append-only. The memo and reliability checklist remain pending human sign-off; the Guntur reviewer must explicitly record that they also reviewed `memo.md` in their note before its status is updated.

### Process a new monthly export

Clean the new month’s orders using the same cleaning rules and load those cleaned orders into `pharmeasy.db`. Keep the saved previous-month summary in `state.json`. Then run:

```bash
python3 metrics_engine.py --month 2026-07 --state-path state.json --db-path pharmeasy.db
```

This computes the new month against the saved previous month and advances the persisted state. Do not run the dataset generator for a real new-month export: it recreates the fixed April–June demonstration dataset. The supplied dashboard and storyline describe that demonstration period; extending them to July requires updating their period-specific presentation.

### Verified checkpoints (from a clean run)
2,159 raw rows → 59 duplicates removed → 2,100 clean · 16 raw region strings → 9 canonical · 94 profit and 48 category values imputed (0 remain) · LEFT JOIN 2,101 vs INNER JOIN 2,100 (Kurnool: `COUNT(*)` = 1 vs `COUNT(order_id)` = 0) · no duplicate `order_id` · flags at 8%: Apr→May 7 of 9 (Vijayawada, Nellore not flagged), May→Jun 7 of 9 (Nellore, Bengaluru not flagged) · 8 unique regions in the CII drafts.

## 2. Cover note (4-artifact package)

**Headline:** Guntur's sales rose +122.19% from April to May 2026 (INR 62,442.27 → INR 138,738.93), the largest swing in the data, associated with more orders and higher average order value; three categories account for 89.22% of the increase while company sales rose 2.89%.

**The 4 artifacts**
- **Streamlit dashboard** (`app.py`): live data exploration with a region filter across overview, category and detail levels.
- **CII narrative** (embedded in the dashboard): what the data means, per flagged region, with its review-gate status and the live approve / edit / reject controls.
- **One-page memo** (`memo.md`): the recommendation, with every claim risk-tagged.
- **Presentation storyline** (`presentation_storyline.md`): how to defend it live (SCR for executives, OCD for regional managers, plus pushback Q&A).

**Consume in this order:** dashboard → CII narrative (inside it) → memo → storyline.

**Single unverified assumption to flag upfront** (from memo.md, Assumptions): monthly exports are complete and consistent; April’s low order count reflects actual orders rather than missing records.

## 3. Repository map
`generate_dataset.py` · `clean_data.py` (+ `validate_schema`) · `data_quality_report.md` · `build_db.py` · `queries.py` · `metrics_engine.py` (flagging + JSON state) · `draft_report.py` · `memo.md` · `review_gate.py` · `audit_log.jsonl` · `reliability_checklist.md` · `app.py` · `presentation_storyline.md` · `run_pipeline.py` · `requirements.txt`
