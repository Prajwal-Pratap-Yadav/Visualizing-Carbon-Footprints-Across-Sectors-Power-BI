# Refresh and Desktop review

`make setup && make run` reproduces the audited CSV exports without Power BI. `make setup-dev && make reproduce` regenerates the companion report, figure, dictionary, insights and actual notebook stdout. Run `make setup-inspect && make inspect` for an independent read-only catalog/cache check. Reproduction requires Python 3.11 or 3.12 and the fixed source already included.

## Original report — manual

1. Copy `powerbi/original/carbon-footprints.pbix` before opening it in Windows Power BI Desktop. Preserve the original checksum.
2. Review the extracted Power Query in [catalog.json](../reports/model/catalog.json). Its original `File.Contents` path is machine-specific. Point the copy to the retained raw CSV and keep DD/MM/YYYY locale parsing explicit.
3. Confirm four pages, cached source grain and all original calculated tables/columns. Audit every total and rank for country/aggregate overlap; the original dense rank includes WORLD and composites.
4. Refresh the copy, verify the model, and export two or three genuine page images. Record Desktop version, date, refreshed source checksum and actual outputs before adding screenshots.

These Desktop actions have **not been executed** here. No companion image is a Power BI export.

## Reviewed companion model — proposed

Import `data/processed/normalized_all.csv` into an `Emissions` table with ISO date types and decimal-number amounts. Use explicit `geography_key` categories and single-select geography controls. Add the proposed [DAX catalog](dax-measures.md), a marked Calendar table and its one-to-many single-direction date relationship. Never aggregate WORLD and partition components together. Compare actual DAX outputs with the cited pandas/decimal values before calling the model validated. A PBIP export is a roadmap item for diff-friendly review, not a generated file in this release.
