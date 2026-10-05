# Reliability Checklist for memo.md

Workflow: safety check → validation → critique/refine → human sign-off.

1. **Safety check:** The memo and CII drafts contain aggregate region/category evidence, with no customer names, addresses or contact information; possible external causes are identified as hypotheses.
2. **Validation:** The memo’s sales, order counts, average order values, category contributions and top-five shares were checked against SQL queries over `pharmeasy.db`; `queries.py` prints the reproducible memo evidence alongside the regional metrics.
3. **Critique/refine:** The recommendation now distinguishes all May Guntur orders from the contributing categories, treats lower top-five concentration as limited evidence, and avoids claiming a market-wide explanation or excluding incomplete source records.
4. **Human sign-off:** The memo remains pending until a human reviewer examines the current Guntur draft and memo, supplies their name and a substantive note, and records approval for the current content hash; the stakeholder view remains blocked until all eight current drafts are approved.

**Status: pending human sign-off.** Technical validation is not a human approval. A Guntur narrative decision does not automatically certify that its separate Markdown memo was read: the reviewer must explicitly include memo review in the note.
