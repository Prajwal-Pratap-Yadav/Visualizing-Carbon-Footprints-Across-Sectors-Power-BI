# Carbon accounting methodology

## What the numbers represent

The input is an archived set of daily estimates for six named sectors: Domestic Aviation, Ground Transport, Industry, International Aviation, Power and Residential. Values are interpreted as MtCO2, with the exact unit caveat in [DATA](DATA.md). Multiplication by 1,000,000 adds a tCO2 column; it changes the numeric scale, not the scientific estimate.

CO2 is not CO2e. A global-warming-potential horizon is therefore not applied. The referenced Carbon Monitor fossil-fuel/cement method supports a territorial-like activity interpretation rather than consumption accounting; the uploaded snapshot's precise release lineage is unverified. Land-use, land-use change and forestry sit outside that referenced scope. No separately named shipping sector appears; its inclusion and allocation are unknown. International aviation allocation is also unproven for this vintage. These limits prevent comparisons that silently mix inventories, gases or accounting bases.

## Reconcile spatial scope before aggregating

For each date and sector, compare the provided WORLD series with the eight-region candidate partition. Preserve the signed difference and all component values. A check passes when:

`abs(WORLD − partition_sum) ≤ max(0.000001 MtCO2, 0.00001 × max(WORLD, partition_sum))`.

This symmetric tolerance is a declared arithmetic/rounding policy. It is not an instrument error bar or a scientific validation threshold. All 9,672 checks pass; the maximum absolute gap is 0.000136 interpreted MtCO2. The [residual CSV](../reports/reconciliation.json) is regenerated as `data/processed/spatial_residuals.csv`; no failed or successful row is hidden.

The six-sector total is a **derived sum**. The source has no independent reported all-sector total against which that sum could be validated. Passing spatial reconciliation therefore validates internal accounting consistency only. Summing every label across the complete snapshot gives 2.054054692198218266… × WORLD because aggregates and their constituents overlap.

## Compare equivalent calendar windows

Complete-year YoY uses adjacent full calendar years only. The fixed source covers complete 2019–2022, followed by 151 days of 2023. The report displays 2023 as Jan–May YTD, never an annual estimate. Matched YTD uses January 1–May 31 in each comparison year; leap-year 2020 retains 152 days. February-end cutoffs clamp to the valid date in non-leap years.

Sector shares use one geography and one date window as the denominator. A zero total returns unavailable shares. CAGR uses complete 2019 and 2022 endpoints over three year intervals, excludes 2023 and is null for an invalid/zero start. Seven-day rolling means require seven consecutive calendar dates; incomplete or gapped windows return unavailable values. None of these descriptive changes demonstrates a causal driver or policy effect.

## Arithmetic and implementation evidence

Input decimals and accounting use a 40-digit local decimal context with bounded exponents and precision. CSV exports preserve original decimal values and deterministic ordering. Charts and browser display convert values to floating point only for presentation. An independent raw-CSV checker uses a separate 50-digit decimal calculation to verify every exported grain, spatial residual, annual/monthly/YTD total and sector share. The optional original-model inspection separately cross-checks annual totals, 2022 YoY/shares, complete-year CAGR and the latest strict seven-day mean with pandas; [values](../reports/model/arithmetic-crosschecks.json) are not Power BI or DAX engine outputs.

Coverage of the source does not imply coverage of all global emissions sources or agreement with a government inventory. No uncertainty interval, per-capita analysis or current-emissions claim is produced from missing metadata.
