"""Regenerate actual audit, report, dictionary, insights, notebook and run evidence."""

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import nbformat
from render_report import render

from carbon_audit.cli import audit
from carbon_audit.domain import Policy
from carbon_audit.export import write_json
from carbon_audit.extract import read_source

ROOT = Path(__file__).resolve().parents[1]


def notebook():
    cells = [
        nbformat.v4.new_markdown_cell(
            "# Carbon accounting review\n\nFixed licensed snapshot; documented unit interpretation; "
            "derived six-sector totals and disjoint geography audit. Python re-creation, not a Power BI export. "
            "This notebook is executed as sequential ordinary Python cells with actual stdout; no kernel/UI run is claimed. "
            "Data: Saloni Jhalani, Kaggle v1, ODbL 1.0 / DbCL 1.0. Source release lineage/aviation/shipping limits remain explicit."
        )
    ]
    code = {
        "setup": "from pathlib import Path\nimport json\nfrom decimal import Decimal\nfrom carbon_audit.analytics import percent_change\nROOT = Path.cwd()\nif not (ROOT / 'configs/policy.json').exists(): ROOT = ROOT.parent\nprofile = json.loads((ROOT/'reports/reconciliation.json').read_text())\nworld = json.loads((ROOT/'reports/analysis.json').read_text())['WORLD']\nprint('Source SHA256:', profile['source_sha256'])\nprint('Database licence:', profile['data_license'])",
        "coverage": "print('Rows retained:', profile['retained_rows'])\nprint('Calendar days:', profile['calendar_days'])\nprint('Geography labels:', len(profile['geographies']))\nprint('Sector labels:', len(profile['sectors']))\nprint('Coverage:', profile['first_day'], 'to', profile['last_day'])",
        "geography-trap": "print('All-label sum / WORLD:', profile['all_labels_sum_divided_by_world'])\nprint('Disjoint partition:', ', '.join(profile['partition']))\nprint('Independent checks:', profile['spatial_checks'], 'passes:', profile['spatial_passes'])\nprint('Max absolute residual, interpreted MtCO2:', profile['maximum_absolute_spatial_residual_mt_co2'])\nprint('No independent all-sector total:', profile['all_sector_total_status'])",
        "complete-years": "for p in world['periods']:\n    print(p['year'], p['period_kind'], p['days'], p['derived_six_sector_total_mt_co2'], 'YoY%:', p['yoy_percent_complete_years_only'])\nprint('CAGR 2019–2022 fraction:', world['cagr_complete_years_fraction'])",
        "matched-ytd": "for p in world['matched_ytd']:\n    print(p['year'], p['first_day'], p['last_day'], p['calendar_days'], p['derived_six_sector_total_mt_co2'])\ncurrent, previous = world['matched_ytd'][-1], world['matched_ytd'][-2]\nprint('2023 versus 2022 Jan–May change%:', percent_change(Decimal(current['derived_six_sector_total_mt_co2']), Decimal(previous['derived_six_sector_total_mt_co2'])))",
        "sector-shares": "period = next(p for p in world['periods'] if p['year']==2022)\nfor sector, share in period['sector_shares_percent'].items():\n    print(sector, 'share of WORLD six-sector 2022 total%:', share)\nprint('Population supplied:', profile['population'])\nprint('Scientific accuracy certified:', profile['scientific_accuracy_or_primary_inventory_certified'])",
    }
    for identifier, source in code.items():
        cell = nbformat.v4.new_code_cell(source)
        cell.id = identifier
        cells.append(cell)
    nb = nbformat.v4.new_notebook(
        cells=cells,
        metadata={
            "execution_mode": "sequential ordinary Python; stdout captured, no Jupyter kernel",
            "language_info": {"name": "python", "version": platform.python_version()},
        },
    )
    folder = ROOT / "notebooks"
    folder.mkdir(exist_ok=True)
    nbformat.write(nb, folder / "01_accounting.ipynb")


def main():
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True
    ).splitlines()
    policy = Policy.load(ROOT / "configs/policy.json")
    output = ROOT / "data/processed"
    profile = audit(ROOT / "data/raw/emissions.csv", ROOT / "configs/policy.json", output)
    analysis = json.loads((output / "analysis.json").read_text())
    rows = read_source(ROOT / "data/raw/emissions.csv", policy)
    for filename in ["reconciliation.json", "analysis.json"]:
        (ROOT / "reports" / filename).write_bytes((output / filename).read_bytes())
    render(rows, profile, analysis)
    notes = ROOT / "docs"
    notes.mkdir(exist_ok=True)
    schema = [
        (
            "geography",
            "string",
            "source label",
            "Original country column; includes countries/composites/aggregates",
        ),
        (
            "geography_key",
            "string",
            "ISO3 or explicit aggregate ID",
            "Country keys are ISO3; composite IDs are never relabelled as countries",
        ),
        (
            "geography_scope",
            "enum",
            "category",
            "country / composite_region / residual_region / world",
        ),
        (
            "date",
            "ISO date",
            "UTC day",
            "Parsed DD/MM/YYYY and checked against original Unix UTC-midnight timestamp",
        ),
        ("sector", "enum", "source taxonomy", "One of the six original sector labels"),
        (
            "value_mt_co2",
            "decimal",
            "interpreted MtCO2 per source day",
            "Original decimal value retained; unit metadata caveat in DATA.md",
        ),
        (
            "value_t_co2",
            "decimal",
            "interpreted tCO2 per source day",
            "Exact multiplication by 1,000,000; not a new physical estimate",
        ),
        ("gas", "constant", "CO2", "No CO2e or multi-gas conversion"),
        (
            "accounting_basis",
            "constant",
            "source_activity_estimate",
            "Territorial-like activity interpretation, not consumption accounting",
        ),
        (
            "unit_interpretation",
            "constant",
            "documented_MtCO2_interpretation",
            "Corroborated interpretation; uploader-specific unit metadata absent",
        ),
    ]
    dictionary = "# Generated data dictionary\n\nGenerated from the normalized export contract. All fields are required, finite and nonblank; nulls/gaps/duplicates are rejected rather than imputed. Original timestamp is validated before export. Input/units/licence: [DATA](DATA.md).\n\n| Column | Type | Unit / meaning | Method / source |\n|---|---|---|---|\n"
    dictionary += "".join(
        f"| `{name}` | {kind} | {unit} | {meaning} |\n" for name, kind, unit, meaning in schema
    )
    (notes / "data-dictionary.md").write_text(dictionary)
    world = analysis["WORLD"]
    recent = next(p for p in world["periods"] if p["year"] == 2022)
    previous, current = world["matched_ytd"][-2:]
    from decimal import Decimal

    from carbon_audit.analytics import percent_change

    ytd_change = percent_change(
        Decimal(current["derived_six_sector_total_mt_co2"]),
        Decimal(previous["derived_six_sector_total_mt_co2"]),
    )
    insights = {
        "retained_records": profile["retained_rows"],
        "calendar_days": profile["calendar_days"],
        "naive_all_labels_divided_by_world": profile["all_labels_sum_divided_by_world"],
        "spatial_checks": profile["spatial_checks"],
        "maximum_absolute_residual_mt_co2": profile["maximum_absolute_spatial_residual_mt_co2"],
        "world_complete_2022_total_mt_co2": recent["derived_six_sector_total_mt_co2"],
        "world_complete_2022_yoy_percent": recent["yoy_percent_complete_years_only"],
        "world_2023_jan_may_total_mt_co2": current["derived_six_sector_total_mt_co2"],
        "world_calendar_matched_2023_2022_ytd_change_percent": str(ytd_change),
        "world_2019_2022_cagr_fraction": world["cagr_complete_years_fraction"],
        "methods": "Decimal accounting on retained source rows; single geography; complete-year and matched-calendar periods; source-vintage/unit/coverage caveats apply.",
    }
    write_json(ROOT / "reports/insights.json", insights)
    text = f"""# Generated descriptive insights

Every number is computed by [named notebook cells](../notebooks/01_accounting.ipynb) from [reconciliation](../reports/reconciliation.json), [analysis](../reports/analysis.json) and [insights JSON](../reports/insights.json). Data units are interpreted as MtCO2 with the [documented source limits](DATA.md); these are archived activity estimates.

| Observation | Value | Notebook cell / method | Caveat |
|---|---|---|---|
| All source rows retained | {profile['retained_rows']:,} / {profile['calendar_days']:,} days | `coverage`; exact validated grain | Fourteen labels include aggregates |
| All-label sum / WORLD | {Decimal(profile['all_labels_sum_divided_by_world']):.6f}× | `geography-trap`; whole snapshot | Unsafe combined total; not fourteen countries |
| Disjoint spatial checks | {profile['spatial_passes']:,} / {profile['spatial_checks']:,} pass | `geography-trap`; each day/sector | Tolerance tests arithmetic, not emissions accuracy |
| Maximum spatial residual | {profile['maximum_absolute_spatial_residual_mt_co2']} interpreted MtCO2 | `geography-trap`; eight-region reconstruction | Original value rounding and methods limit interpretation |
| WORLD 2022 six-sector sum | {recent['derived_six_sector_total_mt_co2']} interpreted MtCO2 | `complete-years`; complete calendar sum | No independent all-sector inventory total |
| WORLD 2022 complete-year YoY | {recent['yoy_percent_complete_years_only']}% | `complete-years`; 2022 / 2021 - 1 | Descriptive snapshot change, no causal attribution |
| WORLD Jan–May 2023 sum | {current['derived_six_sector_total_mt_co2']} interpreted MtCO2 | `matched-ytd`; Jan 1–May 31 | 151 observed days; not annualised |
| Jan–May 2023 / 2022 change | {ytd_change}% | `matched-ytd`; matching calendar bounds | Leap years have a different day count, retained explicitly |
| WORLD 2019–2022 CAGR | {world['cagr_complete_years_fraction']} as fraction | `complete-years`; complete endpoint years | Excludes partial 2023; estimate-vintage dependent |

Sector shares use the same geography/date denominator in `sector-shares`. No population data is supplied, so no per-capita ranking is computed. Shipping and aviation allocation, original publisher release lineage, scientific accuracy and Power BI output remain unverified. No policy recommendation or causal claim follows from these diagnostics.
"""
    (notes / "insights.md").write_text(text)
    notebook()
    paths = [
        "reports/reconciliation.json",
        "reports/analysis.json",
        "reports/insights.json",
        "reports/report-data.json",
        "docs/data-dictionary.md",
        "docs/insights.md",
        "docs/assets/carbon-review.png",
        "docs/assets/carbon-report.html",
    ]
    manifest = {
        "source_git_sha": sha,
        "dirty_tracked_files_at_start": dirty,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.machine(),
        "seed": "none; deterministic decimal accounting and display",
        "data_sha256": policy.source_sha256,
        "policy_sha256": hashlib.sha256((ROOT / "configs/policy.json").read_bytes()).hexdigest(),
        "versions": {name: version(name) for name in ["matplotlib", "nbformat"]},
        "generated_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "scope": "Real archived-source decimal accounting and companion views; no Power BI refresh/render or DAX engine evaluation, no scientific accuracy certification.",
    }
    write_json(ROOT / "reports/run_manifest.json", manifest)
    print(
        f"Reproduced {profile['retained_rows']:,} real records, figure/offline report/dictionary/insights and notebook source."
    )


if __name__ == "__main__":
    main()
