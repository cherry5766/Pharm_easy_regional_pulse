# Recommendation Memo

Risk tags: **[LOW]** structural/logical claim · **[MEDIUM]** reasoned inference specific to this context · **[HIGH]** specific number that must trace to the Part 2 SQL output (`queries.py`, `metrics_engine.py`).

## Title
Guntur's April→May sales jump of +122.19%: what the order data supports, and what it does not. [HIGH]

## Context
- Guntur is one of 9 active regions with orders in the April–June 2026 export, and its April→May change is the largest-magnitude flagged swing in the dataset (+122.19%, versus +99.12% for Visakhapatnam May→June and +66.87% for Tirupati April→May). [HIGH]
- The 8% flag is a fixed operational alert rule, not a statistical significance test, so it signals "a human should look", not "something has changed". [LOW]
- Seven of nine regions crossed the 8% threshold in each transition, so Guntur stands out by size of swing, not by being flagged. [HIGH]

## Key Insight
Guntur's May increase came from both more orders and larger orders, concentrated in three higher-priced categories, while company-wide sales stayed almost flat, so this is a regional shift rather than a market-wide one. [MEDIUM]

## Evidence
- Guntur sales: INR 62,442.27 (April) → INR 138,738.93 (May), an increase of INR 76,296.66 (+122.19%). [HIGH]
- Distinct orders: 51 → 77 (+50.98%). [HIGH]
- Average order value: INR 1,224.36 → INR 1,801.80 (+47.16%). [HIGH]
- Wellness & Nutrition rose from INR 19,297.59 to INR 53,085.01 (+INR 33,787.42), Medical Devices from INR 9,490.63 to INR 32,766.69 (+INR 23,276.06), and Lab Tests from INR 12,578.92 to INR 23,590.94 (+INR 11,012.02); together these three account for 89.22% of the increase. [HIGH]
- Orders in those three categories rose from 14 to 29. [HIGH]
- The five largest Guntur orders made up 38.17% of April sales and 27.46% of May sales, so the jump is not explained by a handful of unusually large orders. [HIGH]
- Company-wide sales moved from INR 1,072,207.16 to INR 1,103,140.73 (+2.89%) over the same transition; excluding Guntur they fell 4.49%. [HIGH]
- Guntur's share of company sales went from 5.82% to 12.58%. [HIGH]
- June sales fell back to INR 99,745.18 (−28.11% vs May) but remained 59.74% above April. [HIGH]
- Because the May level was not fully reversed in June, a one-month data glitch is less likely than a genuine, partly persistent change in order flow. [MEDIUM]

## Recommendation
- Treat the May jump as a real but unexplained increase: do not reset Guntur targets, inventory or staffing on May alone. [MEDIUM]
- Ask the Guntur regional lead to review all May orders, focusing on Wellness & Nutrition, Medical Devices and Lab Tests, and record any known cause; any suggested cause remains unverified. [MEDIUM]
- Use the July export as the confirming test before any structural decision. [MEDIUM]

## Next Check
- When the July export is processed through the pipeline, compare Guntur's July sales with June's INR 99,745.18 and April's INR 62,442.27. [HIGH]
- A July figure at or above June's level supports a sustained shift; a figure near April's level supports a one-off month. [MEDIUM]
- The regional lead's order review should be complete before the July run so both inputs are available together. [LOW]

## Assumptions
- **Unverified assumption (flagged upfront):** the export is complete and consistent for every month, so April's low Guntur order count (51) reflects real demand rather than orders lost in the nightly sync. [MEDIUM]
- **Hypothesis, not fact:** the increase reflects higher volume of high-ticket orders in three categories; the data cannot say *why* volume rose (demand, promotion, availability or otherwise), and no external cause is asserted here. [MEDIUM]
- 94 of 2,100 profit values were imputed using category mean margin, so any profit-margin reading is indicative only; the sales-based figures above do not depend on imputation. [HIGH]
- Order-level analysis is limited to the fields in the export (date, region, category, product, quantity, sales, profit); no customer-level data is used. [LOW]
