"""Comparable calendar periods and safe single-geography time intelligence."""

import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, localcontext
from typing import Any

from carbon_audit.domain import GEOGRAPHIES, SECTORS, AuditError, Observation, precise_sum


def select(rows: list[Observation], geography: str) -> list[Observation]:
    """One geography at a time prevents a country/aggregate multi-select from inflating totals."""
    if geography not in GEOGRAPHIES:
        raise AuditError("Select one supported geography label")
    selected = [row for row in rows if row.geography == geography]
    if not selected:
        raise AuditError("Selected geography is absent from the source")
    return selected


def percent_change(current: Decimal, previous: Decimal) -> Decimal | None:
    """Return a percentage, with an explicit null for a zero denominator."""
    if previous == 0:
        return None
    with localcontext() as context:
        context.prec = 40
        return (current / previous - 1) * 100


def cagr(start: Decimal, end: Decimal, years: int) -> Decimal | None:
    """Use complete endpoint years only; return a fraction, not a percentage."""
    if years <= 0:
        raise AuditError("CAGR requires a positive integer year interval")
    if start <= 0 or end < 0:
        return None
    with localcontext() as context:
        context.prec = 40
        return (end / start) ** (Decimal(1) / Decimal(years)) - 1


def daily_series(rows: list[Observation], geography: str) -> list[tuple[date, Decimal]]:
    """Derived six-sector daily totals; not an independent reported all-sector inventory."""
    days: dict[date, list[Decimal]] = defaultdict(list)
    sectors: dict[date, set[str]] = defaultdict(set)
    for row in select(rows, geography):
        if row.sector in sectors[row.day]:
            raise AuditError("Duplicate sector in daily series")
        sectors[row.day].add(row.sector)
        days[row.day].append(row.mt_co2)
    if any(group != set(SECTORS) for group in sectors.values()):
        raise AuditError("Daily totals require all six source sectors")
    return [(day, precise_sum(values)) for day, values in sorted(days.items())]


def rolling_mean(
    series: list[tuple[date, Decimal]], days: int = 7
) -> list[tuple[date, Decimal | None]]:
    """Require a full calendar window; never treat missing days as adjacent observations."""
    if not 1 <= days <= 366:
        raise AuditError("Rolling window must be 1–366 calendar days")
    values = dict(series)
    if len(values) != len(series):
        raise AuditError("Duplicate date in rolling series")
    result: list[tuple[date, Decimal | None]] = []
    with localcontext() as context:
        context.prec = 40
        for day in sorted(values):
            window = [day - timedelta(days=offset) for offset in range(days)]
            mean = (
                precise_sum([values[d] for d in window]) / days
                if all(d in values for d in window)
                else None
            )
            result.append((day, mean))
    return result


def periods(rows: list[Observation], geography: str) -> list[dict[str, Any]]:
    """Keep partial periods separate; YoY exists only between adjacent complete years."""
    selected = select(rows, geography)
    grouped: dict[int, list[Observation]] = defaultdict(list)
    for row in selected:
        grouped[row.day.year].append(row)
    output = []
    complete: dict[int, Decimal] = {}
    with localcontext() as context:
        context.prec = 40
        for year, group in sorted(grouped.items()):
            days = {row.day for row in group}
            first, last = min(days), max(days)
            is_complete = (
                first == date(year, 1, 1)
                and last == date(year, 12, 31)
                and len(days) == (366 if calendar.isleap(year) else 365)
            )
            total = precise_sum([row.mt_co2 for row in group])
            sector_totals = {
                sector: precise_sum([r.mt_co2 for r in group if r.sector == sector])
                for sector in SECTORS
            }
            yoy = (
                percent_change(total, complete[year - 1])
                if is_complete and year - 1 in complete
                else None
            )
            if is_complete:
                complete[year] = total
            output.append(
                {
                    "geography": geography,
                    "year": year,
                    "first_day": first.isoformat(),
                    "last_day": last.isoformat(),
                    "days": len(days),
                    "complete_year": is_complete,
                    "period_kind": (
                        "full_calendar_year" if is_complete else "partial_calendar_period"
                    ),
                    "derived_six_sector_total_mt_co2": str(total),
                    "yoy_percent_complete_years_only": None if yoy is None else str(yoy),
                    "sector_totals_mt_co2": {k: str(v) for k, v in sector_totals.items()},
                    "sector_shares_percent": {
                        k: None if total == 0 else str(v / total * 100)
                        for k, v in sector_totals.items()
                    },
                }
            )
    return output


def matched_ytd(rows: list[Observation], geography: str) -> list[dict[str, Any]]:
    """Compare January 1 through the source's final month/day; preserve leap-year length."""
    selected = select(rows, geography)
    end = max(row.day for row in selected)
    result = []
    for year in sorted({row.day.year for row in selected}):
        cutoff = date(year, end.month, min(end.day, calendar.monthrange(year, end.month)[1]))
        days = {row.day for row in selected if row.day.year == year and row.day <= cutoff}
        expected = (cutoff - date(year, 1, 1)).days + 1
        if len(days) != expected:
            raise AuditError("Matched YTD requires complete January-to-cutoff coverage")
        total = precise_sum(
            [row.mt_co2 for row in selected if row.day.year == year and row.day <= cutoff]
        )
        result.append(
            {
                "year": year,
                "first_day": date(year, 1, 1).isoformat(),
                "last_day": cutoff.isoformat(),
                "calendar_days": len(days),
                "derived_six_sector_total_mt_co2": str(total),
            }
        )
    return result
