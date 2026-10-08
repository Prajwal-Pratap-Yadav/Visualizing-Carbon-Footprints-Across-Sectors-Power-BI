"""Independently recompute archived grains and report arithmetic from the raw CSV."""

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
profile = json.loads((ROOT / "reports/reconciliation.json").read_text())
analysis = json.loads((ROOT / "reports/analysis.json").read_text())
projection = json.loads((ROOT / "reports/report-data.json").read_text())
raw = ROOT / "data/raw/emissions.csv"
assert hashlib.sha256(raw.read_bytes()).hexdigest() == profile["source_sha256"]
source = {}
annual = defaultdict(Decimal)
monthly = defaultdict(Decimal)
with localcontext() as context:
    context.prec = 50
    with raw.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            day = datetime.strptime(row["date"], "%d/%m/%Y").date()
            key = (row["country"], day.isoformat(), row["sector"])
            assert key not in source, "Duplicate raw grain"
            value = Decimal(row["value"])
            source[key] = value
            annual[(row["country"], day.year)] += value
            monthly[(row["country"], day.year, day.month, row["sector"])] += value
    assert len(source) == profile["retained_rows"] == 135408
    partition = {"Brazil", "China", "EU27 & UK", "India", "Japan", "Russia", "US", "ROW"}
    expected_membership = {
        "normalized_all.csv": set(source),
        "world.csv": {k for k in source if k[0] == "WORLD"},
        "nonoverlapping_regions.csv": {k for k in source if k[0] in partition},
    }
    for name, expected in expected_membership.items():
        path = ROOT / "data/processed" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == profile["csv_sha256"][name]
        seen = set()
        with path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                key = (row["geography"], row["date"], row["sector"])
                assert key not in seen and key in expected, name
                seen.add(key)
                assert Decimal(row["value_mt_co2"]) == source[key]
                assert Decimal(row["value_t_co2"]) == source[key] * 1000000
                assert row["gas"] == "CO2"
                assert row["geography_key"] == profile["geographies"][key[0]]["key"]
                assert row["geography_scope"] == profile["geographies"][key[0]]["scope"]
        assert seen == expected, name
    residuals = []
    with (ROOT / "data/processed/spatial_residuals.csv").open(newline="") as stream:
        seen = set()
        for row in csv.DictReader(stream):
            pair = (row["date"], row["sector"])
            assert pair not in seen
            seen.add(pair)
            world = source[("WORLD", *pair)]
            reconstructed = sum(source[(g, *pair)] for g in partition)
            difference = world - reconstructed
            tolerance = max(Decimal("0.000001"), Decimal("0.00001") * max(world, reconstructed))
            assert Decimal(row["world_mt_co2"]) == world
            assert Decimal(row["partition_mt_co2"]) == reconstructed
            assert Decimal(row["difference_mt_co2"]) == difference
            assert Decimal(row["tolerance_mt_co2"]) == tolerance
            assert row["passed"] == str(abs(difference) <= tolerance).lower()
            residuals.append(abs(difference))
    assert len(residuals) == profile["spatial_checks"] == 9672
    assert max(residuals) == Decimal(profile["maximum_absolute_spatial_residual_mt_co2"])
    assert abs(
        sum(source.values()) / sum(v for (g, _, _), v in source.items() if g == "WORLD")
        - Decimal(profile["all_labels_sum_divided_by_world"])
    ) < Decimal("1e-37")
    for geography, result in analysis.items():
        for period in result["periods"]:
            year = period["year"]
            total = annual[(geography, year)]
            assert total == Decimal(period["derived_six_sector_total_mt_co2"])
            assert period["complete_year"] == (year < 2023)
            if year == 2023:
                assert period["days"] == 151 and period["yoy_percent_complete_years_only"] is None
            elif year > 2019:
                yoy = (total / annual[(geography, year - 1)] - 1) * 100
                assert abs(yoy - Decimal(period["yoy_percent_complete_years_only"])) < Decimal(
                    "1e-35"
                )
            display = projection["views"][geography]["periods"][str(year)]
            assert Decimal(display["total"]) == total and display["days"] == period["days"]
            for month in display["months"]:
                month_number = int(month["month"][-2:])
                values = [
                    monthly[(geography, year, month_number, s)] for s in projection["sectors"]
                ]
                assert [Decimal(v) for v in month["sectors"]] == values
                assert Decimal(month["total"]) == sum(values)
            for sector, share in period["sector_shares_percent"].items():
                sector_total = sum(
                    v
                    for (g, y, _, s), v in monthly.items()
                    if g == geography and y == year and s == sector
                )
                assert abs(sector_total / total * 100 - Decimal(share)) < Decimal("1e-35")
        for period in result["matched_ytd"]:
            value = sum(
                v
                for (g, y, month, _), v in monthly.items()
                if g == geography and y == period["year"] and month <= 5
            )
            assert value == Decimal(period["derived_six_sector_total_mt_co2"])
            assert period["calendar_days"] == (152 if period["year"] == 2020 else 151)
manifest = json.loads((ROOT / "reports/run_manifest.json").read_text())
for name, expected_hash in manifest["generated_sha256"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected_hash, name
nb = nbformat.read(ROOT / "notebooks/01_accounting.ipynb", as_version=4)
nbformat.validate(nb)
cells = [c for c in nb.cells if c.cell_type == "code"]
assert len(cells) == 6 and [c.execution_count for c in cells] == list(range(1, 7))
assert all(c.outputs and all(o.output_type == "stream" for o in c.outputs) for c in cells)
outputs = "\n".join(o.text for c in cells for o in c.outputs)
for text in [profile["source_sha256"], "135408", "9672", "151", "not supplied", "False"]:
    assert text in outputs, text
print(
    "Independent raw-grain/export/spatial/annual/monthly/YTD/share checks and actual notebook/hash evidence pass."
)
