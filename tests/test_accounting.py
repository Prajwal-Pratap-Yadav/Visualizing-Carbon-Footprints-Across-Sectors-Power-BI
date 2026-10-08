"""Adversarial extraction and independent accounting/time-window checks."""

import csv
import hashlib
import json
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from carbon_audit.analytics import (
    cagr,
    daily_series,
    matched_ytd,
    percent_change,
    periods,
    rolling_mean,
    select,
)
from carbon_audit.cli import audit, main
from carbon_audit.domain import (
    PARTITION,
    AuditError,
    Observation,
    Policy,
    decimal_value,
    precise_sum,
)
from carbon_audit.extract import read_source
from carbon_audit.reconcile import reconcile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/carbon_audit/fixtures"


@pytest.fixture
def policy():
    return Policy.load(FIXTURE / "policy.json")


@pytest.fixture
def rows(policy):
    return read_source(FIXTURE / "emissions.csv", policy)


def write_source(tmp_path, records, policy, headers=None):
    path = tmp_path / "input.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=headers or ["country", "date", "sector", "value", "timestamp"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(records)
    return path, replace(policy, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


@pytest.fixture
def source_records():
    with (FIXTURE / "emissions.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize(
    "text",
    [
        "NaN",
        "Infinity",
        "-1",
        "1e100",
        "1e-100",
        "9" * 41,
        "1.123456789012345678901",
        "not-a-number",
    ],
)
def test_invalid_decimal_is_rejected(text):
    with pytest.raises(AuditError):
        decimal_value(text)


def test_decimal_zero_and_tonnes_are_exact():
    assert decimal_value("0e-999999") == Decimal(0)
    assert Observation("Brazil", date(2019, 1, 1), "Power", Decimal("0.096799")).t_co2 == Decimal(
        "96799"
    )
    assert precise_sum([Decimal("1000000000000"), Decimal("0.000000000001")]) == Decimal(
        "1000000000000.000000000001"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("country", "EU27"),
        ("sector", "Agriculture"),
        ("date", "01/13/2019"),
        ("date", "2019-01-01"),
        ("date", "1/1/2019"),
        ("timestamp", "1546300801"),
        ("timestamp", ""),
        ("value", "-0.1"),
        ("value", "NaN"),
        ("value", "1e50"),
    ],
)
def test_bad_source_fields_are_rejected(tmp_path, policy, source_records, field, value):
    source_records[0][field] = value
    source, changed = write_source(tmp_path, source_records, policy)
    with pytest.raises(AuditError):
        read_source(source, changed)


def test_checksum_is_verified_before_loading(policy, tmp_path):
    path = tmp_path / "tampered.csv"
    path.write_bytes((FIXTURE / "emissions.csv").read_bytes() + b"\n")
    with pytest.raises(AuditError, match="checksum"):
        read_source(path, policy)


def test_surplus_field_and_non_utf8_are_rejected(tmp_path, policy):
    for content in [
        b"country,date,sector,value,timestamp\nBrazil,01/01/2019,Power,1,1546300800,extra\n",
        b"\xff",
    ]:
        path = tmp_path / "bad.csv"
        path.write_bytes(content)
        changed = replace(policy, source_sha256=hashlib.sha256(content).hexdigest())
        with pytest.raises(AuditError):
            read_source(path, changed)


def test_ordered_schema_and_empty_source_are_rejected(tmp_path, policy, source_records):
    source, changed = write_source(
        tmp_path, source_records, policy, ["date", "country", "sector", "value", "timestamp"]
    )
    with pytest.raises(AuditError, match="headers"):
        read_source(source, changed)
    source, changed = write_source(tmp_path, [], policy)
    with pytest.raises(AuditError, match="no observations"):
        read_source(source, changed)


def test_canonical_duplicate_and_missing_sector_are_rejected(tmp_path, policy, source_records):
    duplicate = dict(source_records[0], country=" Brazil ")
    source, changed = write_source(tmp_path, source_records + [duplicate], policy)
    with pytest.raises(AuditError, match="Duplicate"):
        read_source(source, changed)
    source, changed = write_source(tmp_path, source_records[1:], policy)
    with pytest.raises(AuditError, match="Missing daily sector"):
        read_source(source, changed)


@pytest.mark.parametrize(
    "key,value",
    [
        ("gas", "CO2e"),
        ("source_unit", "tCO2"),
        ("gwp_horizon", "AR6-100"),
        ("accounting_basis", "consumption"),
        ("lulucf", "included"),
        ("shipping_treatment", "included"),
        ("relative_tolerance", "0.05"),
        ("source_sha256", "bogus"),
        ("synthetic", "false"),
        ("data_creator", ""),
        ("last_day", "2099-01-01"),
    ],
)
def test_unsupported_policy_cannot_silently_change_interpretation(tmp_path, key, value):
    raw = json.loads((FIXTURE / "policy.json").read_text())
    raw[key] = value
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(AuditError):
        Policy.load(path)


def test_unknown_or_duplicate_policy_geographies_are_rejected(tmp_path):
    raw = json.loads((FIXTURE / "policy.json").read_text())
    for labels in [
        raw["geographies"] + ["Brazil"],
        ["WORLD"],
        raw["geographies"] + ["Atlantis"],
        "WORLD",
    ]:
        raw["geographies"] = labels
        path = tmp_path / "bad-policy.json"
        path.write_text(json.dumps(raw))
        with pytest.raises(AuditError):
            Policy.load(path)


def test_world_reconciliation_detects_a_changed_independent_total(rows, policy):
    residuals = reconcile(rows, policy)
    assert len(residuals) == 12 and all(r.passed and r.difference == 0 for r in residuals)
    changed = [
        (
            replace(r, mt_co2=Decimal("37"))
            if r.geography == "WORLD" and r.day == date(2019, 1, 1) and r.sector == "Power"
            else r
        )
        for r in rows
    ]
    failures = [r for r in reconcile(changed, policy) if not r.passed]
    assert len(failures) == 1 and failures[0].difference == 1


def test_reconciliation_rejects_missing_and_duplicate_regions(rows, policy):
    for bad in [rows + [rows[0]], [r for r in rows if r.geography != "ROW"]]:
        with pytest.raises(AuditError):
            reconcile(bad, policy)


def test_single_geography_selection_prevents_aggregate_multiselect(rows):
    assert len(select(rows, "WORLD")) == 12
    assert all(r.geography == "Brazil" for r in select(rows, "Brazil"))
    for label in ["ALL", "WORLD,EU27 & UK", "France"]:
        with pytest.raises(AuditError):
            select(rows, label)
    assert not set(PARTITION) & {"France", "Germany", "Italy", "Spain", "UK"}


def test_daily_totals_require_all_sectors(rows):
    assert daily_series(rows, "WORLD") == [
        (date(2019, 1, 1), Decimal(216)),
        (date(2019, 1, 2), Decimal(216)),
    ]
    with pytest.raises(AuditError):
        daily_series(rows + [rows[0]], rows[0].geography)
    with pytest.raises(AuditError):
        daily_series([r for r in rows if r.sector != "Residential"], "WORLD")


def test_rolling_mean_uses_calendar_windows_and_known_arithmetic():
    start = date(2020, 1, 1)
    series = [(start + timedelta(days=i), Decimal(i + 1)) for i in range(8)]
    result = rolling_mean(series)
    assert [v for _, v in result[:6]] == [None] * 6
    assert result[6][1] == 4 and result[7][1] == 5
    assert rolling_mean(series[:3] + series[4:])[-1][1] is None
    for bad in [0, 367]:
        with pytest.raises(AuditError):
            rolling_mean(series, bad)
    with pytest.raises(AuditError):
        rolling_mean(series + [series[0]])


def test_percentage_and_cagr_have_known_results_and_zero_limits():
    assert percent_change(Decimal(110), Decimal(100)) == 10
    assert percent_change(Decimal(1), Decimal(0)) is None
    assert abs(cagr(Decimal(100), Decimal("133.1"), 3) - Decimal("0.1")) < Decimal("1e-35")
    assert cagr(Decimal(0), Decimal(1), 2) is None
    assert cagr(Decimal(100), Decimal(0), 2) == -1
    with pytest.raises(AuditError):
        cagr(Decimal(100), Decimal(100), 0)


def test_partial_calendar_year_never_gets_an_annual_yoy(rows):
    record = periods(rows, "WORLD")[0]
    assert record["complete_year"] is False
    assert record["yoy_percent_complete_years_only"] is None
    assert sum(Decimal(v) for v in record["sector_shares_percent"].values()) == pytest.approx(
        Decimal(100)
    )


def test_matched_ytd_preserves_leap_calendar_lengths():
    records = []
    for year, days in [(2019, 59), (2020, 60)]:
        for offset in range(days):
            records.append(
                Observation("WORLD", date(year, 1, 1) + timedelta(days=offset), "Power", Decimal(1))
            )
    result = matched_ytd(records, "WORLD")
    assert [r["calendar_days"] for r in result] == [59, 60]
    assert result[0]["last_day"] == "2019-02-28"
    assert result[1]["last_day"] == "2020-02-29"
    with pytest.raises(AuditError):
        matched_ytd(records[1:], "WORLD")


def test_export_and_synthetic_scope_are_deterministic(tmp_path):
    first = audit(FIXTURE / "emissions.csv", FIXTURE / "policy.json", tmp_path / "first")
    second = audit(FIXTURE / "emissions.csv", FIXTURE / "policy.json", tmp_path / "second")
    assert first == second
    assert first["retained_rows"] == 108 and first["spatial_checks"] == 12
    assert first["synthetic"] is True and first["data_license"] == "MIT"
    assert first["scientific_accuracy_or_primary_inventory_certified"] is False
    assert first["all_labels_sum_divided_by_world"] == "2"
    for name, digest in first["csv_sha256"].items():
        content = (tmp_path / "first" / name).read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest
        assert content == (tmp_path / "second" / name).read_bytes()


def test_real_snapshot_retains_all_rows_and_avoids_partial_year_claims(tmp_path):
    profile = audit(ROOT / "data/raw/emissions.csv", ROOT / "configs/policy.json", tmp_path)
    assert profile["retained_rows"] == 135408 and profile["spatial_checks"] == 9672
    assert profile["spatial_failures"] == 0 and profile["calendar_days"] == 1612
    assert profile["maximum_absolute_spatial_residual_mt_co2"] == "0.000136"
    assert Decimal(profile["all_labels_sum_divided_by_world"]) > 2
    analysis = json.loads((tmp_path / "analysis.json").read_text())["WORLD"]
    assert [p["year"] for p in analysis["periods"] if p["complete_year"]] == [
        2019,
        2020,
        2021,
        2022,
    ]
    assert analysis["periods"][-1]["yoy_percent_complete_years_only"] is None
    assert [r["calendar_days"] for r in analysis["matched_ytd"]] == [151, 152, 151, 151, 151]
    assert len(list(csv.DictReader((tmp_path / "nonoverlapping_regions.csv").open()))) == 77376
    assert len(list(csv.DictReader((tmp_path / "world.csv").open()))) == 9672


def test_cli_demo_and_rejection_status(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["carbon-audit", "--demo", "--output", str(tmp_path / "demo")])
    assert main() == 0
    assert "108 rows retained" in capsys.readouterr().out
    monkeypatch.setattr("sys.argv", ["carbon-audit", "--input", str(tmp_path / "missing")])
    assert main() == 2 and "Audit rejected" in capsys.readouterr().err
