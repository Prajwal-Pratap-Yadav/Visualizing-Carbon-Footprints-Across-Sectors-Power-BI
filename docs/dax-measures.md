# Original expressions and proposed DAX companion

The preserved PBIX was inspected read-only with PBIXRay 0.15.5. It has **zero explicit measures**, three calculated tables, thirteen calculated columns, four report pages and 25 native visuals. [Full catalog](../reports/model/catalog.json) contains the extracted Power Query, table/column expressions and visual bindings. The original dense geography rank includes WORLD, ROW and the European composite; it is not a country-only leaderboard. Two auto-date tables are not a reviewed marked-calendar model. Zero relationships were extracted.

The [companion formulas](../powerbi/companion/measures.dax) are **proposed, uninstalled and not evaluated in a DAX engine**. They require the separately imported audited `normalized_all.csv`, an `Emissions` table, a marked `Calendar` table spanning complete calendar years, its one-to-many single-direction date relationship, and a single-select `Emissions[geography_key]`. Use Calendar fields for every date slicer; direct fact-date filters break the intended date replacement semantics. Retain decimal-number values rather than currency's four-decimal rounding. The strict fixed-source audit supplies coverage guarantees; a future source must pass that audit before these formulas are used.

| Proposed formula | Purpose / formatting | Independent Python/pandas observation | Limit |
|---|---|---|---|
| `Calendar`, `Year` | Contiguous 2019–2023 dates, marked table; integer year | Validated source has 1,612 observed days | Calendar includes unobserved June–December 2023 |
| `Scoped amount MtCO2` | Sum in one geography/date/sector context; `#,##0.00` | Every retained source decimal is checked | Blank for zero/multiple geography keys |
| `Six-sector sum MtCO2` | Remove sector filter, retain geography/date; `#,##0.00` | WORLD 2022: 36,119.462025 | Derived total, not independent inventory |
| `Snapshot last day` | Latest observation ignoring calendar/sector filters; ISO date | 2023-05-31 | Fixed source vintage |
| `Sector share` | Selected sector / six-sector sum; `0.00%` | WORLD 2022 Power: 39.29246617841894% (pandas) | Same geography/date denominator; zero gives blank |
| `Complete-year YoY` | Adjacent complete years; `+0.00%;-0.00%;0.00%` | WORLD 2022: +1.7220917512825284% (pandas) | Blank for partial 2023; coverage contract required |
| `Calendar-matched YTD YoY` | Jan 1 through snapshot month/day in both years; percent | WORLD 2023/2022 Jan–May: +0.3414029434995725…% (decimal) | Leap-year lengths retained; not annualized |
| `Strict seven-day mean MtCO2` | Exactly seven observed calendar-day totals; `#,##0.00` | WORLD ending 2023-05-31: 92.60729042857143 (pandas) | Blank on missing/unobserved dates |
| `Complete 2019-2022 CAGR` | Fixed complete endpoint years; `0.00%` | WORLD: 0.007257168767901279 fraction (pandas) | Excludes 2023; not a forecast |

Actual independent arithmetic values are in [arithmetic-crosschecks.json](../reports/model/arithmetic-crosschecks.json), [analysis](../reports/analysis.json) and [insights](../reports/insights.json). Decimal versus pandas differences stay within the explicit tolerances in `scripts/check_model.py`; the latest seven-day mean is also checked. This agreement is **not validation against Power BI output**. Installing formulas, testing blank/zero/multiselect/date-boundary behavior, refreshing and capturing genuine Desktop outputs remain roadmap work.

Microsoft's primary references support the formula semantics: [HASONEVALUE](https://learn.microsoft.com/en-us/dax/hasonevalue-function-dax), [REMOVEFILTERS](https://learn.microsoft.com/en-us/dax/removefilters-function-dax), [inclusive DATESBETWEEN](https://learn.microsoft.com/en-us/dax/datesbetween-function-dax) and [AVERAGEX](https://learn.microsoft.com/en-us/dax/averagex-function-dax). They are measure formulas, not visual calculations. The checked-in file is a review catalog, not a deployment script.
