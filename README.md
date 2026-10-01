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

**Human review is never automatic.** `run_pipeline.py` does not call the review gate, so every CII draft shows as *awaiting human review* on the dashboard until a person decides, either **in the dashboard** (open a region in *Insight Narrative* → optional reviewer note → click ✅ Approve / ✏️ Edit / 🚫 Reject) or via `python3 review_gate.py --review` (or `--review --region Guntur --decision approve --note "..."`). `audit_log.jsonl` is append-only; the test harness's entries carry `run_id=test-harness` and are ignored by the dashboard, so they can never count as an approval.

### Verified checkpoints (from a clean run)
2,159 raw rows → 59 duplicates removed → 2,100 clean · 16 raw region strings → 9 canonical · 94 profit and 48 category values imputed (0 remain) · LEFT JOIN 2,101 vs INNER JOIN 2,100 (Kurnool: `COUNT(*)` = 1 vs `COUNT(order_id)` = 0) · no duplicate `order_id` · flags at 8%: Apr→May 7 of 9 (Vijayawada, Nellore not flagged), May→Jun 7 of 9 (Nellore, Bengaluru not flagged) · 8 unique regions in the CII drafts.

## 2. Cover note (4-artifact package)

**Headline:** Guntur's sales rose +122.19% from April to May 2026 (INR 62,442.27 → INR 138,738.93), the largest swing in the data, driven by more orders and larger baskets in Wellness & Nutrition, Medical Devices and Lab Tests while company-wide sales stayed flat.

**The 4 artifacts**
- **Streamlit dashboard** (`app.py`): live data exploration with a region filter across overview, category and detail levels.
- **CII narrative** (embedded in the dashboard): what the data means, per flagged region, with its review-gate status and the live approve / edit / reject controls.
- **One-page memo** (`memo.md`): the recommendation, with every claim risk-tagged.
- **Presentation storyline** (`presentation_storyline.md`): how to defend it live (SCR for executives, OCD for regional managers, plus pushback Q&A).

**Consume in this order:** dashboard → CII narrative (inside it) → memo → storyline.

**Single unverified assumption to flag upfront** (from memo.md, Assumptions): the export is complete and consistent for every month, so April's low Guntur order count (51) reflects real demand rather than orders lost in the nightly sync.

## 3. Repository map
`generate_dataset.py` · `clean_data.py` (+ `validate_schema`) · `data_quality_report.md` · `build_db.py` · `queries.py` · `metrics_engine.py` (flagging + JSON state) · `draft_report.py` · `memo.md` · `review_gate.py` · `audit_log.jsonl` · `reliability_checklist.md` · `app.py` · `presentation_storyline.md` · `run_pipeline.py` · `requirements.txt`
