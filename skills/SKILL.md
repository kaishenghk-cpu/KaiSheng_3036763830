---
name: replicate-minimum-wage
description: Rebuild the Card and Krueger 1994 survey replication, ownership extension, tables, figures and report from the authorized course CSV. Use for rerunning or validating this project.
---

# Replicate the minimum wage project

1. Work from the repository root, one level above this skills directory.
2. Read README.md and data/raw/DATA_DICTIONARY.md. Obtain authorized Package 01 input; do not infer missing values from the published tables.
3. Place the unmodified public.csv at data/raw/01_DID/data/public.csv, preserving the numbered directory and filename. Alternatively use 01_DID/data/public.csv at the root. Keep the supplied input_manifest.json; stop and explain any checksum mismatch rather than disabling the check.
4. Install requirements.txt in an isolated Python environment and run `python code/run_all.py`.
5. Inspect outputs/validation.json, outputs/tables/original_comparison.csv and the rendered report. Verify that all 410 rows remain, the balanced employment sample has 384 rows, and Table 4 has 357 rows.
6. Preserve the distinction between permanently closed stores (follow-up employment zero), temporarily closed stores (missing in the baseline), and ordinary item nonresponse. Do not deduplicate on SHEET alone.
7. Check that estimated outputs derive from the input. Keep benchmark values confined to comparisons and assertions. Disclose the remaining model 5 coefficient difference and the Table 2 wage-threshold difference.
8. Interpret the ownership interaction with its confidence interval. Do not turn a nonsignificant estimate into a claim of equal effects, and do not claim that store-level HC1 errors resolve two-state policy inference.
9. Keep restricted raw and processed rows out of Git. Regenerate them locally after authorized input access. Commit meaningful changes to this project without inventing earlier work history.

Use code/analysis.py for transformations and estimation and code/build_report.py for report generation. Keep code/run_all.py as the single entry point. Do not manually edit generated tables or figures.
