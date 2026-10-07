# Generated descriptive insights

Every number is computed by [named notebook cells](../notebooks/01_accounting.ipynb) from [reconciliation](../reports/reconciliation.json), [analysis](../reports/analysis.json) and [insights JSON](../reports/insights.json). Data units are interpreted as MtCO2 with the [documented source limits](DATA.md); these are archived activity estimates.

| Observation | Value | Notebook cell / method | Caveat |
|---|---|---|---|
| All source rows retained | 135,408 / 1,612 days | `coverage`; exact validated grain | Fourteen labels include aggregates |
| All-label sum / WORLD | 2.054055× | `geography-trap`; whole snapshot | Unsafe combined total; not fourteen countries |
| Disjoint spatial checks | 9,672 / 9,672 pass | `geography-trap`; each day/sector | Tolerance tests arithmetic, not emissions accuracy |
| Maximum spatial residual | 0.000136 interpreted MtCO2 | `geography-trap`; eight-region reconstruction | Original value rounding and methods limit interpretation |
| WORLD 2022 six-sector sum | 36119.462025 interpreted MtCO2 | `complete-years`; complete calendar sum | No independent all-sector inventory total |
| WORLD 2022 complete-year YoY | 1.722091751282524785698328312287454501100% | `complete-years`; 2022 / 2021 - 1 | Descriptive snapshot change, no causal attribution |
| WORLD Jan–May 2023 sum | 15113.988959 interpreted MtCO2 | `matched-ytd`; Jan 1–May 31 | 151 observed days; not annualised |
| Jan–May 2023 / 2022 change | 0.341402943499572511286449115021404277200% | `matched-ytd`; matching calendar bounds | Leap years have a different day count, retained explicitly |
| WORLD 2019–2022 CAGR | 0.007257168767901222570901751422143415965 as fraction | `complete-years`; complete endpoint years | Excludes partial 2023; estimate-vintage dependent |

Sector shares use the same geography/date denominator in `sector-shares`. No population data is supplied, so no per-capita ranking is computed. Shipping and aviation allocation, original publisher release lineage, scientific accuracy and Power BI output remain unverified. No policy recommendation or causal claim follows from these diagnostics.
