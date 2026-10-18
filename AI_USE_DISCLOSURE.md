# AI use disclosure

ChatGPT Codex was used to assist with interpreting the project requirements and paper, developing and debugging Python code, preparing tables and figures, and drafting the report. The main uses and checks are documented below.

| Stage | AI assistance | Validation during preparation |
| --- | --- | --- |
| Research design | Clarifying the replication tasks and developing an ownership extension | Checked the assigned tables against the original article; replaced an initial wage-group extension because it overlapped with the original analysis. |
| Data preparation | Writing code for variable construction and sample selection | Preserved the input checksum; verified 410 rows, closure classifications, the 384-store balanced sample and the 357-store regression sample. |
| Estimation | Implementing regressions, standard errors and sensitivity checks | Checked OLS normal equations and the DID identity; independently verified the baseline slope and standard error using SciPy. |
| Reporting | The author prepared an independent report draft. AI helped revise the language and format the tables, and also contributed draft explanations during preparation. | Compared calculated results with published tables; reported discrepancies and uncertainty rather than changing data to force agreement. |

Important corrections included retaining permanently closed stores at zero follow-up employment, preserving distinct restaurants with the same SHEET number, and correcting the standard-error calculation for changes in available-case means. The model 5 discrepancy remains disclosed: the reconstruction gives 11.98 (7.42), compared with 11.91 (7.39) in the article.

The workflow was rerun from a separate clean-input directory, and the generated outputs matched byte for byte. The report does not interpret nonsignificant ownership estimates as proof of equal effects, or store-level robust standard errors as resolving inference with only two states.

These checks were performed during AI-assisted preparation and are recorded in the code and validation outputs. Responsibility for reviewing the submitted analysis, its assumptions and its interpretation remains with the author.
