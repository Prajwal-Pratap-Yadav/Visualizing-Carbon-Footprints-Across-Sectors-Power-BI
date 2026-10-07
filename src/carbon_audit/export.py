"""Deterministic attributed database exports and inspectable accounting diagnostics."""

import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from carbon_audit.analytics import cagr, matched_ytd, periods
from carbon_audit.domain import GEOGRAPHIES, PARTITION, SECTORS, Observation, Policy, precise_sum
from carbon_audit.reconcile import Residual


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def write_rows(path: Path, rows: list[Observation]) -> str:
    """Retain the all-label table; separate geography scope from the original country field."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "geography",
                "geography_key",
                "geography_scope",
                "date",
                "sector",
                "value_mt_co2",
                "value_t_co2",
                "gas",
                "accounting_basis",
                "unit_interpretation",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.geography,
                    row.geography_key,
                    row.geography_scope,
                    row.day.isoformat(),
                    row.sector,
                    str(row.mt_co2),
                    str(row.t_co2),
                    "CO2",
                    "source_activity_estimate",
                    "documented_MtCO2_interpretation",
                ]
            )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(
    rows: list[Observation], residuals: list[Residual], policy: Policy, output: Path
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, selected in [
        ("normalized_all.csv", rows),
        ("nonoverlapping_regions.csv", [r for r in rows if r.geography in PARTITION]),
        ("world.csv", [r for r in rows if r.geography == "WORLD"]),
    ]:
        hashes[name] = write_rows(output / name, selected)
    residual_path = output / "spatial_residuals.csv"
    with residual_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "date",
                "sector",
                "world_mt_co2",
                "partition_mt_co2",
                "difference_mt_co2",
                "tolerance_mt_co2",
                "passed",
            ]
        )
        for r in residuals:
            writer.writerow(
                [
                    r.day.isoformat(),
                    r.sector,
                    r.world,
                    r.partition,
                    r.difference,
                    r.tolerance,
                    str(r.passed).lower(),
                ]
            )
    hashes[residual_path.name] = hashlib.sha256(residual_path.read_bytes()).hexdigest()
    world_sum = precise_sum([r.mt_co2 for r in rows if r.geography == "WORLD"])
    all_sum = precise_sum([r.mt_co2 for r in rows])
    with localcontext() as context:
        context.prec = 40
        ratios = [
            abs(r.difference) / max(r.world, r.partition)
            for r in residuals
            if max(r.world, r.partition) != 0
        ]
        naive_ratio = None if world_sum == 0 else str(all_sum / world_sum)
    report = {
        "source_sha256": policy.source_sha256,
        "source_rows": len(rows),
        "retained_rows": len(rows),
        "first_day": policy.first_day.isoformat(),
        "last_day": policy.last_day.isoformat(),
        "calendar_days": (policy.last_day - policy.first_day).days + 1,
        "geographies": {
            g: {"key": GEOGRAPHIES[g][0], "scope": GEOGRAPHIES[g][1], "rows": n}
            for g, n in sorted(Counter(r.geography for r in rows).items())
        },
        "sectors": list(SECTORS),
        "all_daily_sector_coverage_complete": True,
        "partition": list(PARTITION),
        "spatial_checks": len(residuals),
        "spatial_passes": sum(r.passed for r in residuals),
        "spatial_failures": sum(not r.passed for r in residuals),
        "absolute_tolerance_mt_co2": str(policy.absolute_tolerance),
        "relative_tolerance": str(policy.relative_tolerance),
        "maximum_absolute_spatial_residual_mt_co2": str(max(abs(r.difference) for r in residuals)),
        "maximum_relative_spatial_residual": str(max(ratios, default=Decimal(0))),
        "all_labels_sum_divided_by_world": naive_ratio,
        "all_sector_total_status": "derived sum of six sectors; no independent all-sector total in source",
        "accounting_basis": "source_activity_estimate; territorial-like interpretation, not consumption-based inventory",
        "gas": "CO2; not CO2e",
        "unit": "MtCO2 interpretation corroborated by original model and Carbon Monitor display; uploader metadata absent",
        "lulucf": "outside referenced fossil-fuel/cement scope",
        "gwp_horizon": "not applicable to CO2-only data",
        "shipping": "no separately named sector; inclusion/allocation unverified",
        "international_aviation_allocation": "source convention not proven for original snapshot",
        "population": "not supplied; no per-capita result computed",
        "data_creator": policy.data_creator,
        "data_license": policy.data_license,
        "source_url": policy.source_url,
        "synthetic": policy.synthetic,
        "csv_sha256": hashes,
        "scientific_accuracy_or_primary_inventory_certified": False,
    }
    write_json(output / "reconciliation.json", report)
    analysis: dict[str, dict[str, Any]] = {
        g: {"periods": periods(rows, g), "matched_ytd": matched_ytd(rows, g)}
        for g in policy.geographies
    }
    for result in analysis.values():
        complete = [p for p in result["periods"] if p["complete_year"]]
        rate = (
            cagr(
                Decimal(complete[0]["derived_six_sector_total_mt_co2"]),
                Decimal(complete[-1]["derived_six_sector_total_mt_co2"]),
                complete[-1]["year"] - complete[0]["year"],
            )
            if len(complete) > 1
            else None
        )
        result["cagr_complete_years_fraction"] = None if rate is None else str(rate)
    write_json(output / "analysis.json", analysis)
    return report
