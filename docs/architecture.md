# Architecture and operating contract

The dependency-free `carbon_audit` runtime separates strict extraction, explicit geography/accounting policy, spatial reconciliation, calendar analysis and deterministic export. The command-line entry point writes all retained data plus review diagnostics. Exit code 0 means the declared spatial checks pass, 1 means a residual fails tolerance and 2 means input/policy validation fails. Scientific accuracy is outside this contract.

Developer-only matplotlib and nbformat generate the real-data plot, standalone offline HTML and executed ordinary-Python notebook. Node/Chromium are optional review tools for interaction, accessibility and actual screenshots; none is needed for `make run`. PBIXRay runs in a separate read-only environment to avoid coupling the package to binary inspection dependencies. No service, cloud account or external runtime data fetch is required.

Each export keeps the all-label dataset. Separate WORLD and nonoverlapping-region exports make intended accounting scope explicit. The HTML provides one geography selector and a full-year/YTD selector, a numeric table behind its monthly chart and source/scientific limitations beside the metrics. Generated `report-data.json` contains exact decimal strings; presentation rounding cannot change exported results.

The wheel includes only code and an invented MIT packaging fixture. Source/evidence archives contain attributed real data under ODbL/DbCL. Read-only inspection never rewrites the original PBIX. Source data has no person-level records; the original owner's local import path is redacted in the text catalog and preserved in the original binary.
