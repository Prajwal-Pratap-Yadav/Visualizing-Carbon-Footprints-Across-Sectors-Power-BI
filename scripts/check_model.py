"""Require an unchanged preserved model and compare independent pandas arithmetic."""

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from carbon_audit.analytics import daily_series, rolling_mean
from carbon_audit.domain import Policy
from carbon_audit.extract import read_source

ROOT = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1])
for filename in ["catalog.json", "arithmetic-crosschecks.json"]:
    assert json.loads((output / filename).read_text()) == json.loads(
        (ROOT / "reports/model" / filename).read_text()
    ), filename
analysis = json.loads((ROOT / "data/processed/analysis.json").read_text())["WORLD"]
cross = json.loads((output / "arithmetic-crosschecks.json").read_text())
for p in analysis["periods"]:
    assert abs(
        Decimal(p["derived_six_sector_total_mt_co2"])
        - Decimal(str(cross["pandas_world_annual_mt_co2"][str(p["year"])]))
    ) < Decimal("1e-8")
    if p["year"] == 2022:
        assert abs(
            Decimal(p["yoy_percent_complete_years_only"])
            - Decimal(str(cross["pandas_world_complete_2022_yoy_percent"]))
        ) < Decimal("1e-10")
        for sector, share in p["sector_shares_percent"].items():
            assert abs(
                Decimal(share)
                - Decimal(str(cross["pandas_world_2022_sector_shares_percent"][sector]))
            ) < Decimal("1e-10")
assert abs(
    Decimal(analysis["cagr_complete_years_fraction"])
    - Decimal(str(cross["pandas_world_complete_2019_2022_cagr_fraction"]))
) < Decimal("1e-12")
policy = Policy.load(ROOT / "configs/policy.json")
rows = read_source(ROOT / "data/raw/emissions.csv", policy)
latest = rolling_mean(daily_series(rows, "WORLD"))[-1]
assert latest[0] == date(2023, 5, 31) and latest[1] is not None
assert abs(
    latest[1] - Decimal(str(cross["pandas_world_latest_strict_7_day_mean_mt_co2"]))
) < Decimal("1e-12")
print(
    "Original model drift and independent pandas annual/share/YoY/CAGR/strict-seven-day cross-checks pass; no DAX output claim."
)
