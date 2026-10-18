# AI use disclosure

This project was prepared with substantial assistance from ChatGPT Codex on 18 October 2026. AI assisted with interpreting course instructions, reading the source article, planning the ownership extension, writing Python code, calculating and interpreting results, generating figures, and drafting the report and documentation. This is not a claim that the student independently wrote every line of code or text.

## Verification completed during preparation

- Checked the original Table 2, Table 3, Table 4 and Figure 1 against the author-hosted published article.
- Read the course README and data dictionary and preserved the original CSV bytes; the SHA-256 value is recorded in input_manifest.json.
- Verified 410 rows, the 331/79 state split, closure statuses, 384 balanced employment observations and the 357-store Table 4 sample.
- Checked that a difference of state means equals the corresponding OLS slope, that the OLS normal equations hold, and that SciPy's independent simple-regression implementation matches the baseline slope and conventional standard error.
- Compared estimated main coefficients with the published values. Models 1 to 4 match at two decimals. Model 5 differs: 11.98 (7.42) instead of 11.91 (7.39). This is disclosed and has not been fully resolved.
- Examined the effect of HC1 standard errors and alternative samples. Nonsignificant ownership results are retained and interpreted as inconclusive.
- Ran the complete workflow and reviewed rendered report pages for layout. Detailed checks and package versions are recorded in outputs/validation.json.

## Important corrections and rejected suggestions

1. The initially proposed extension compared stores by initial wage. This already overlaps with the original paper and assigned replication; it was replaced with a company-ownership interaction.
2. Requiring observed follow-up wages for every store drops permanently closed restaurants and produces 351 rather than 357 observations. The code now retains permanent closures with zero follow-up FTE while requiring valid baseline wages.
3. SHEET is not unique by itself. Dropping duplicate SHEET values would remove a legitimate restaurant in another state and chain. The original rows are preserved.
4. An ordinary full-time headcount share does not reconstruct the printed percentage. The numerical convention 100 x EMPFT / FTE does; its unusual interpretation is made explicit rather than relabelled as a standard headcount share.
5. The first implementation reused balanced-change standard errors for the available-case change-in-means row. This was replaced with a delta-method estimate for the actual available-case statistic, retaining within-store covariance. Remaining differences from the printed standard errors are disclosed.
6. A positive point estimate was not treated as definitive causal proof. The restricted baseline has p about 0.052 with conventional standard errors and about 0.110 with HC1. Neither accounts for state-level policy shocks with only two states.

## Scope of the checks

These are checks executed or reviewed by the assistant during preparation. They are not a representation that the student personally verified every formula, reviewed every code line, or reran the project independently. The student should review the final report, input choices, code, and interpretation before submission and remains responsible for the project.

No empirical outcomes were invented. Published benchmark values are isolated in comparison and validation code and are not substituted for estimates. The project uses the supplied course data; it does not claim a separate WRDS or Princeton data acquisition. No fabricated historical commits or backdated work stages were created.
