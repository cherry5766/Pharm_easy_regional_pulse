# Reliability Checklist for memo.md

Workflow: safety check → validation → critique/refine → human sign-off.

1. **Safety check:** I confirmed memo.md and the CII drafts contain only region-level and category-level aggregates from `orders_clean`: no customer names, addresses, phone numbers or other personal data, and no external market claims.
2. **Validation:** I re-derived every INR figure, percentage and order count in memo.md from `pharmeasy.db` with SQL (region × month sums, `COUNT(DISTINCT order_id)`, category splits, top-5 order shares) and matched them to `queries.py` and `metrics_engine.py` output to the second decimal.
3. **Critique/refine:** On review I tested the "a few huge orders drove it" explanation, found the top-5 order share was higher in April (38.17%) than May (27.46%), and rewrote the insight to say the jump is broad-based volume, labelling the cause as a hypothesis in Assumptions.
4. **Human sign-off:** memo.md stays *pending* until a named human reviewer records (with the dashboard's Approve / Edit / Reject buttons, or via `python3 review_gate.py --review`) `approve` for Guntur with a note in `audit_log.jsonl` under the real run_id; nothing in the pipeline approves it automatically, and `downstream_use_allowed` is only true after that entry.

**Status: pending human sign-off** (update this line once the reviewer has approved).
