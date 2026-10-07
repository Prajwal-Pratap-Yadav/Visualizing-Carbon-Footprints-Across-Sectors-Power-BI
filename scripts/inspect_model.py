"""Extract preserved model expressions and compare cached tables read-only."""

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
from pbixray import PBIXRay

ROOT = Path(__file__).resolve().parents[1]


def records(value):
    """PBIXRay exposes security/connection collections as lists or DataFrames."""
    return value.to_dict("records") if hasattr(value, "to_dict") else value


def inspect(output):
    path = ROOT / "powerbi/original/carbon-footprints.pbix"
    model = PBIXRay(str(path))
    query = model.power_query.to_dict("records")
    for row in query:
        row["Expression"] = re.sub(
            r'File\.Contents\("(?:[^\"]|\"\")*"\)',
            'File.Contents("<LOCAL_SOURCE_PATH_REDACTED>")',
            row["Expression"],
        )
        if "C:\\" in row["Expression"] or "Users\\" in row["Expression"]:
            raise ValueError("Unredacted original source path")
    with zipfile.ZipFile(path) as archive:
        layout = json.loads(archive.read("Report/Layout").decode("utf-16-le"))
    pages = []
    for page in layout["sections"]:
        visuals = []
        for visual in page["visualContainers"]:
            config = json.loads(visual["config"])
            commands = json.loads(visual.get("query", "{}")).get("Commands", [])
            selections = (
                commands[0]
                .get("SemanticQueryDataShapeCommand", {})
                .get("Query", {})
                .get("Select", [])
                if commands
                else []
            )
            visuals.append(
                {
                    "visual_id": config["name"],
                    "type": config.get("singleVisual", {}).get("visualType"),
                    "select": selections,
                }
            )
        pages.append({"name": page["displayName"], "page_id": page["name"], "visuals": visuals})
    cached = model.get_table("Datasets").rename(columns={"value (In Mega Tons)": "value"})
    source = pd.read_csv(ROOT / "data/raw/emissions.csv")
    source["date"] = pd.to_datetime(source["date"], format="%d/%m/%Y")
    merged = source.merge(
        cached,
        on=["country", "date", "sector"],
        suffixes=("_source", "_cache"),
        validate="one_to_one",
    )
    if len(merged) != len(source) or len(source) != len(cached):
        raise ValueError("Original cached/source grains differ")
    summary = model.get_table("summary_of_Carbon_Emissions_for_each_country")
    totals = source.groupby("country").value.sum()
    ordered = totals.sort_values(ascending=False).index.tolist()
    rank_matches = all(
        ordered.index(row["country"]) + 1 == row["Rank"] for row in summary.to_dict("records")
    )
    world = source[source.country == "WORLD"].copy()
    annual = world.groupby(world.date.dt.year).value.sum()
    latest = (
        world.groupby("date").value.sum().sort_index().rolling(7, min_periods=7).mean().iloc[-1]
    )
    shares_2022 = (
        world[world.date.dt.year == 2022].groupby("sector").value.sum() / annual.loc[2022] * 100
    )
    comparison = {
        "scope": "Python/pandas computations and decoded cached tables; not validated against Power BI output or DAX engine evaluation.",
        "source_rows": len(source),
        "cached_rows": len(cached),
        "identical_geography_date_sector_grain": True,
        "maximum_source_cache_value_difference": float(
            (merged.value_source - merged.value_cache).abs().max()
        ),
        "cached_year_date_disagreements": int(
            (cached.Year.astype(int) != cached.date.dt.year).sum()
        ),
        "maximum_source_cached_summary_difference": float(
            max(
                abs(totals[r["country"]] - r["sum of Carbon_Emission"])
                for r in summary.to_dict("records")
            )
        ),
        "cached_dense_rank_matches_python": rank_matches,
        "original_rank_warning": "WORLD, ROW, EU aggregate and countries share the ranking; not a country-only leaderboard.",
        "pandas_world_annual_mt_co2": {str(y): float(v) for y, v in annual.items()},
        "pandas_world_complete_2022_yoy_percent": float(
            (annual.loc[2022] / annual.loc[2021] - 1) * 100
        ),
        "pandas_world_2022_sector_shares_percent": {s: float(v) for s, v in shares_2022.items()},
        "pandas_world_latest_strict_7_day_mean_mt_co2": float(latest),
        "pandas_world_complete_2019_2022_cagr_fraction": float(
            (annual.loc[2022] / annual.loc[2019]) ** (1 / 3) - 1
        ),
        "independent_all_sector_reported_total_available": False,
    }
    catalog = {
        "pbix_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "inspection_tool": "pbixray==0.15.5",
        "tables": list(model.tables),
        "schema": model.schema.to_dict("records"),
        "explicit_dax_measures": model.dax_measures.to_dict("records"),
        "calculated_columns": model.dax_columns.to_dict("records"),
        "calculated_tables": model.dax_tables.to_dict("records"),
        "relationships": model.relationships.to_dict("records"),
        "power_query_sanitized": query,
        "connections": records(model.connections),
        "parameters": records(model.m_parameters),
        "rls": records(model.rls),
        "ols": records(model.ols),
        "cached_geography_summary": summary.sort_values("Rank").to_dict("records"),
        "pages": pages,
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in [("catalog.json", catalog), ("arithmetic-crosschecks.json", comparison)]:
        (output / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
        )
    print(
        f"Read-only original: {len(model.tables)} tables; {len(model.dax_measures)} explicit measures; {len(pages)} pages; cached/source rows match."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/model")
    inspect(parser.parse_args().output)
