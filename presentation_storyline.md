# Presentation Storyline: Guntur April→May +122.19%

One finding, framed twice for two audiences. Every number traces to `queries.py` / `metrics_engine.py` output (Part 2 SQL).

## A. For the executive: Situation → Complication → Resolution

**Situation (what is true today).**
Company-wide sales are steady: INR 1,072,207.16 in April, INR 1,103,140.73 in May and INR 1,089,843.53 in June. Month to month the portfolio looks calm.

**Complication (the surprising or at-risk element).**
Underneath that calm, Guntur's sales more than doubled from April to May: INR 62,442.27 to INR 138,738.93, a +122.19% swing and the largest flagged move in the data. Its share of company sales went from 5.82% to 12.58%. Without Guntur, company sales actually fell 4.49% that month. The increase warrants checking whether existing targets, stock and staffing remain appropriate; a temporary order-mix change would call for a different response. June (INR 99,745.18, −28.11% vs May) has not yet told us which.

**Resolution (recommendation and what happens next).**
Do not reset Guntur targets or stock on May alone. This week, the Guntur regional lead reviews the 77 May orders (especially Wellness & Nutrition, Medical Devices and Lab Tests) and records any known cause. When the July export is processed, we compare it with June's INR 99,745.18 and April's INR 62,442.27: persistence above June supports further investigation, while a return near April weakens the sustained-shift interpretation. Source reconciliation must inform any structural decision. The memo only circulates after a human approves it through the review gate, with the decision logged in `audit_log.jsonl`.

## B. For the regional manager: Overview → Category → Detail

**Overview (the headline number).**
Guntur's sales grew +122.19% from April to May, adding INR 76,296.66. Orders grew 51 → 77 (+50.98%) and average order value grew from INR 1,224.36 to INR 1,801.80 (+47.16%), so both volume and basket size contributed.

**Category (which area drives it).**
Three higher-priced categories account for 89.22% of the increase: Wellness & Nutrition (+INR 33,787.42, 19,297.59 → 53,085.01), Medical Devices (+INR 23,276.06, 9,490.63 → 32,766.69) and Lab Tests (+INR 11,012.02, 12,578.92 → 23,590.94). Orders in those three rose from 14 to 29. OTC and Prescription Medicines rose only modestly.

**Detail (supporting evidence and method).**
The five largest Guntur orders were 38.17% of April sales but 27.46% of May sales, so May sales were less concentrated in those orders. This does not rule out large-order contributions to the increase. June stayed 59.74% above April, so the change was only partly reversed. Method: raw export of 2,159 rows → 59 exact duplicates removed → region text normalised → missing category and profit imputed → loaded to SQLite → sales summed by region and month with SQL → MoM = (current − previous) / previous × 100. The sales figures do not depend on profit imputation; category breakdowns use the deterministic product-to-category recovery. The 8% flag is a fixed alert rule, not a significance test: 7 of 9 regions crossed it in this transition, so Guntur stands out by size, not by being flagged.

## C. Anticipated pushback (Direct Acknowledgement Pattern)

**Q1. "Why should I believe this number?"**
1. *Acknowledge:* A +122% jump in one region is exactly the kind of figure that deserves suspicion, especially because the raw export had duplicates, inconsistent region names and missing values.
2. *Verified vs not:* Verified: duplicates were removed (59 rows), `order_id` is unique after cleaning, and Guntur's sales, order counts and category splits are re-computed from SQL and match the dashboard. Not verified: that the source export itself captured every real April order.
3. *Resolution:* A reconciliation of Guntur's April and May order counts (51 and 77) against the source order system by the regional operations team, within 5 working days of this meeting, would settle it.

**Q2. "What if an alternative explanation is driving this?"**
1. *Acknowledge:* Yes, the data shows what changed (more orders, larger baskets in three categories) but not why, and a campaign, stock availability or a low April base could all be behind it.
2. *Verified vs not:* Verified: top-5 order share fell from 38.17% to 27.46%, showing lower concentration, and company sales increased only 2.89%. Large-order contributions and wider market behaviour are not resolved by these comparisons. Not verified: any specific cause; the memo labels causes as hypotheses only.
3. *Resolution:* The Guntur regional lead lists any promotions, stock events or onboarding activity for April and May within 5 working days; July's Guntur sales then show whether the level persists.

**Q3. "What would change your recommendation?"**
1. *Acknowledge:* The recommendation is deliberately cautious, so it should have clear conditions for changing.
2. *Verified vs not:* Verified: June fell back 28.11% but stayed above April. Not verified: where July lands.
3. *Resolution:* If July Guntur sales persist at or above INR 99,745.18, investigate whether targets and stock should change; a return near INR 62,442.27 weakens that case. Make a decision at the July review only after source reconciliation and the regional lead’s explanation are available.
