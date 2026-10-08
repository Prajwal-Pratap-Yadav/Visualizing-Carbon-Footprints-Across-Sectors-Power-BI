"""Generate an offline interactive report and a real measured-data hero figure."""

import calendar
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from carbon_audit.analytics import percent_change
from carbon_audit.domain import GEOGRAPHIES, PARTITION, SECTORS, Observation, precise_sum
from carbon_audit.export import write_json

ROOT = Path(__file__).resolve().parents[1]
COLORS = ["#a78bfa", "#38bdf8", "#34d399", "#fbbf24", "#fb7185", "#cbd5e1"]


def projection(rows, profile, analysis):
    """Keep exact decimal totals in the data payload; plotting converts only display values."""
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row.geography, row.day.year, row.day.month, row.sector)].append(row.mt_co2)
    monthly = {key: precise_sum(values) for key, values in grouped.items()}
    views = {}
    for geography, result in analysis.items():
        ytd = {p["year"]: p for p in result["matched_ytd"]}
        periods = {}
        for period in result["periods"]:
            year = period["year"]
            change = period["yoy_percent_complete_years_only"]
            if not period["complete_year"] and year - 1 in ytd:
                value = percent_change(
                    Decimal(ytd[year]["derived_six_sector_total_mt_co2"]),
                    Decimal(ytd[year - 1]["derived_six_sector_total_mt_co2"]),
                )
                change = None if value is None else str(value)
            months = []
            for month in range(1, 13):
                if (geography, year, month, SECTORS[0]) not in monthly:
                    continue
                values = [monthly[(geography, year, month, sector)] for sector in SECTORS]
                months.append(
                    {
                        "month": f"{year}-{month:02}",
                        "label": calendar.month_abbr[month],
                        "sectors": [str(v) for v in values],
                        "total": str(precise_sum(values)),
                    }
                )
            periods[str(year)] = {
                "first_day": period["first_day"],
                "last_day": period["last_day"],
                "days": period["days"],
                "complete": period["complete_year"],
                "total": period["derived_six_sector_total_mt_co2"],
                "shares": [period["sector_shares_percent"][s] for s in SECTORS],
                "change": change,
                "months": months,
            }
        views[geography] = {
            "key": GEOGRAPHIES[geography][0],
            "scope": GEOGRAPHIES[geography][1],
            "cagr": result["cagr_complete_years_fraction"],
            "periods": periods,
        }
    order = ["WORLD", "EU27 & UK", "ROW"] + sorted(
        g for g in analysis if GEOGRAPHIES[g][1] == "country"
    )
    return {
        "profile": profile,
        "sectors": list(SECTORS),
        "geography_order": order,
        "views": views,
        "attribution": "Saloni Jhalani, CO2 Emissions by Sectors, Kaggle v1; ODbL 1.0 / DbCL 1.0",
        "scope": "Python re-creation, not a Power BI export. Archived values, documented unit/accounting interpretation.",
    }


def hero(rows: list[Observation], profile, analysis, path):
    """Two accounting comparisons and an observed sector trend, without annualizing YTD."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "text.color": "#e8eff8",
            "axes.labelcolor": "#aec0d7",
            "xtick.color": "#aec0d7",
            "ytick.color": "#aec0d7",
            "axes.edgecolor": "#314056",
            "axes.facecolor": "#111c2e",
            "figure.facecolor": "#0b1220",
            "savefig.facecolor": "#0b1220",
        }
    )
    fig = plt.figure(figsize=(16, 9), dpi=150)
    grid = fig.add_gridspec(
        2, 2, left=0.11, right=0.97, bottom=0.20, top=0.77, hspace=0.60, wspace=0.34
    )
    fig.text(0.06, 0.94, "CARBON / ACCOUNTING REVIEW", color="#38bdf8", fontsize=12, weight="bold")
    fig.text(
        0.06, 0.88, "Reconcile the geography. Then read the trend.", fontsize=25, weight="bold"
    )
    fig.text(
        0.06,
        0.825,
        f"{profile['retained_rows']:,} records retained  |  2019–31 May 2023  |  Six-sector archived snapshot",
        color="#aec0d7",
        fontsize=12,
    )
    ax = fig.add_subplot(grid[0, 0])
    world = precise_sum([r.mt_co2 for r in rows if r.geography == "WORLD"])
    partition = precise_sum([r.mt_co2 for r in rows if r.geography in PARTITION])
    naive = precise_sum([r.mt_co2 for r in rows])
    totals = [float(world), float(partition), float(naive)]
    ax.barh(
        ["WORLD series", "8 disjoint\nregions", "All labels\n(unsafe)"],
        totals,
        color=["#38bdf8", "#34d399", "#fbbf24"],
        height=0.55,
    )
    ax.invert_yaxis()
    ax.set_xlim(0, max(totals) * 1.27)
    for i, total in enumerate(totals):
        ax.text(total + max(totals) * 0.02, i, f"{total:,.0f}", va="center", fontsize=11)
    ax.set_xlabel("Whole-snapshot sum · interpreted Mt CO₂")
    ax.set_title(
        f"01 / All labels sum to {Decimal(profile['all_labels_sum_divided_by_world']):.3f}× WORLD",
        loc="left",
        fontsize=14,
        pad=14,
        weight="bold",
    )
    ax = fig.add_subplot(grid[0, 1])
    periods = analysis["WORLD"]["periods"]
    values = [float(p["derived_six_sector_total_mt_co2"]) for p in periods]
    bars = ax.bar(range(len(periods)), values, color=["#38bdf8"] * 4 + ["#a78bfa"], width=0.6)
    bars[-1].set_hatch("///")
    bars[-1].set_edgecolor("#e8eff8")
    ax.set_xticks(range(len(periods)), ["2019", "2020", "2021", "2022", "2023\nJan–May YTD"])
    ax.set_ylim(0, max(values) * 1.26)
    for i, value in enumerate(values):
        ax.text(i, value + max(values) * 0.035, f"{value:,.0f}", ha="center", fontsize=10)
    ax.set_ylabel("Derived six-sector sum · Mt CO₂")
    ax.set_title(
        "02 / Complete years and YTD stay separate", loc="left", fontsize=14, pad=14, weight="bold"
    )
    ax = fig.add_subplot(grid[1, 0])
    projection_data = projection(rows, profile, analysis)
    months = [m for p in projection_data["views"]["WORLD"]["periods"].values() for m in p["months"]]
    stacks = [[float(m["sectors"][i]) for m in months] for i in range(len(SECTORS))]
    ax.stackplot(range(len(months)), stacks, colors=COLORS, labels=SECTORS)
    ax.set_xlim(0, len(months) - 1)
    ax.set_xticks([0, 12, 24, 36, 48], ["2019", "2020", "2021", "2022", "2023"])
    ax.set_ylabel("Monthly sector sum · Mt CO₂")
    ax.grid(axis="y", alpha=0.12)
    ax.set_title(
        "03 / Observed WORLD monthly sector mix", loc="left", fontsize=14, pad=14, weight="bold"
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=3, fontsize=8, frameon=False)
    ax = fig.add_subplot(grid[1, 1])
    ax.set_axis_off()
    ax.text(
        0,
        0.95,
        "04 / Accounting checks and limits",
        fontsize=14,
        weight="bold",
        va="top",
        transform=ax.transAxes,
    )
    ax.text(
        0,
        0.61,
        f"{profile['spatial_passes']:,} / {profile['spatial_checks']:,}",
        fontsize=30,
        weight="bold",
        color="#34d399",
        transform=ax.transAxes,
    )
    ax.text(
        0,
        0.40,
        "daily sector partition checks pass",
        fontsize=11,
        color="#aec0d7",
        transform=ax.transAxes,
    )
    ax.text(
        0,
        0.29,
        f"Max gap: {profile['maximum_absolute_spatial_residual_mt_co2']} interpreted Mt CO₂\nNo independent all-sector inventory total\nUnit / source-vintage assumptions remain explicit",
        fontsize=10,
        color="#aec0d7",
        linespacing=1.4,
        va="top",
        transform=ax.transAxes,
    )
    for axes in fig.axes:
        for spine in ["top", "right"]:
            axes.spines[spine].set_visible(False)
    fig.text(
        0.06,
        0.045,
        "Python re-creation, not a Power BI export. Saloni Jhalani · Kaggle v1 · ODbL / DbCL. Arithmetic checks do not certify emission estimates.",
        fontsize=9,
        color="#aec0d7",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def render(rows, profile, analysis):
    data = projection(rows, profile, analysis)
    write_json(ROOT / "reports/report-data.json", data)
    template = (ROOT / "scripts/report-template.html").read_text()
    serialized = json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    html = template.replace("__REPORT_DATA__", serialized)
    if "__REPORT_DATA__" in html:
        raise ValueError("Unexpanded report data placeholder")
    assets = ROOT / "docs/assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "carbon-report.html").write_text(html, encoding="utf-8")
    hero(rows, profile, analysis, assets / "carbon-review.png")
