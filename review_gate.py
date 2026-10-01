"""Part 3 - human review gate with append-only audit log.

Usage:
  python3 review_gate.py                 # TEST HARNESS: exercises approve/edit/reject (entries tagged run_id=test-harness)
  python3 review_gate.py --review        # REAL review: a human decides on each draft interactively
  python3 review_gate.py --review --region Guntur --decision approve --note "checked vs SQL"

Nothing in the pipeline approves anything automatically. Drafts stay 'awaiting human review'
on the dashboard until a person records a decision for the current run_id.
"""
import argparse
import copy
import json
import os
from datetime import datetime, timezone

AUDIT_LOG = "audit_log.jsonl"
ALLOWED = ("approve", "edit", "reject")
TEST_RUN_ID = "test-harness"


def review_gate_v1(report, decision, reviewer_note="", audit_path=AUDIT_LOG):
    """Validate decision, return an updated copy of report, append exactly one audit line."""
    if decision not in ALLOWED:
        raise ValueError(f"decision must be one of {ALLOWED}, got {decision!r}")
    if not isinstance(report, dict) or "region" not in report or "run_id" not in report:
        raise ValueError("report must be a dict with 'region' and 'run_id'")
    out = copy.deepcopy(report)
    out["decision"] = decision
    out["reviewer_note"] = reviewer_note
    out["status"] = {"approve": "approved", "edit": "needs_edit", "reject": "rejected"}[decision]
    # only an approved draft may leave the team; an edited draft must be re-submitted and approved
    out["downstream_use_allowed"] = decision == "approve"
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "run_id": report["run_id"], "region": report["region"],
             "decision": decision, "reviewer_note": reviewer_note}
    with open(audit_path, "a") as f:          # append-only: never truncated or rewritten
        f.write(json.dumps(entry) + "\n")
    return out


def load_latest_decisions(run_id, audit_path=AUDIT_LOG):
    """{region: latest entry} for ONE run_id. Test-harness entries never count as real decisions."""
    latest = {}
    if os.path.exists(audit_path):
        with open(audit_path) as f:
            for line in f:
                e = json.loads(line)
                if e["run_id"] == run_id:
                    latest[e["region"]] = e
    return latest


def _test_harness():
    from draft_report import build_drafts
    print("TEST HARNESS - entries are tagged run_id='%s' and are NOT real approvals.\n" % TEST_RUN_ID)
    blocks, _, _ = build_drafts()
    by = {b["region"]: dict(b, run_id=TEST_RUN_ID) for b in blocks}
    cases = [
        ("Guntur", "approve", "[TEST] approve path."),
        ("Visakhapatnam", "edit", "[TEST] edit path: reword implication."),
        ("Karimnagar", "reject", "[TEST] reject path: implication overstated."),
    ]
    for region, decision, note in cases:
        before = by[region]
        after = review_gate_v1(before, decision, note)
        print(f"--- {region}: {decision.upper()} ---")
        print(" BEFORE:", {k: before[k] for k in ("status", "downstream_use_allowed")})
        print(" AFTER: ", {k: after[k] for k in ("status", "decision", "downstream_use_allowed")})
    try:
        review_gate_v1(blocks[0], "maybe")
    except ValueError as e:
        print("\nInvalid decision correctly rejected:", e)


def _real_review(region=None, decision=None, note=""):
    from draft_report import build_drafts
    blocks, _, _ = build_drafts()
    if region:                                   # non-interactive single decision (still a human's command)
        blocks = [b for b in blocks if b["region"].lower() == region.lower()]
        if not blocks:
            raise SystemExit(f"No draft for region {region!r}")
        if decision not in ALLOWED:
            raise SystemExit(f"--decision must be one of {ALLOWED}")
        out = review_gate_v1(blocks[0], decision, note)
        print(f"{out['region']}: {out['status']} (downstream use allowed: {out['downstream_use_allowed']})")
        return
    done = load_latest_decisions(blocks[0]["run_id"])
    for b in blocks:
        print("\n" + "=" * 70)
        print(f"{b['region']}  (already decided: {done[b['region']]['decision']})" if b["region"] in done else b["region"])
        print("Context:    ", b["context"])
        print("Insight:    ", b["insight"])
        print("Implication:", b["implication"])
        while True:
            d = input("Decision [a]pprove / [e]dit / [r]eject / [s]kip / [q]uit: ").strip().lower()
            if d in ("q", "quit"):
                return
            if d in ("s", "skip", ""):
                break
            d = {"a": "approve", "e": "edit", "r": "reject"}.get(d, d)
            if d in ALLOWED:
                n = input("Reviewer note: ").strip()
                out = review_gate_v1(b, d, n)
                print(f" -> {out['status']}; downstream use allowed: {out['downstream_use_allowed']}")
                break
            print("Please enter a, e, r, s or q.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--review", action="store_true", help="record real human decisions")
    p.add_argument("--region")
    p.add_argument("--decision", choices=ALLOWED)
    p.add_argument("--note", default="")
    a = p.parse_args()
    if a.review:
        _real_review(a.region, a.decision, a.note)
    else:
        _test_harness()
