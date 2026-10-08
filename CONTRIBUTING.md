# Contributing

Use Python 3.11 or 3.12 on Linux. Clone the repository and run `make setup-dev`; run `make lint typecheck test docs` before a pull request. `make reproduce` regenerates data-quality evidence and executes the notebook's plain-Python cells. For the separate read-only model catalog, use Python 3.12 and `make setup-inspect inspect`.

Keep a small conventional commit for each reviewed change. Never alter the original CSV/PBIX bytes or rewrite Git history. Input-policy changes require source/license evidence and an explicit before/after record. Retain ODbL/DbCL attribution and applicable database reuse terms. Document unit/accounting interpretation, preserve source vintage and distinguish fixture/cache arithmetic from actual Power BI output.

Tests should explain a real failure mode: duplicate grain, nonfinite/negative/excessive-precision values, source-date/timestamp disagreement, geography overlap, exact tolerance boundaries, partial years, calendar gaps and complete slice membership. New notebook cells must use ordinary Python and explicit printed output; the maintained runner does not support magics/display machinery.

Use [bug reports](https://github.com/Prajwal-Pratap-Yadav/Visualizing-Carbon-Footprints-Across-Sectors-Power-BI/issues/new?template=bug.yml) for reproducibility defects and the existing roadmap for Desktop/provenance work. See [security policy](SECURITY.md) for sensitive findings. Scoped tests and measured evidence are preferred to unverified dashboard or scientific-accuracy claims.
