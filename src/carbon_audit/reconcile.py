"""Reconcile independent WORLD observations against a disjoint region partition."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from carbon_audit.domain import PARTITION, SECTORS, AuditError, Observation, Policy, precise_sum


@dataclass(frozen=True)
class Residual:
    day: date
    sector: str
    world: Decimal
    partition: Decimal
    difference: Decimal
    tolerance: Decimal
    passed: bool


def reconcile(rows: list[Observation], policy: Policy) -> list[Residual]:
    """Check all day/sector pairs; never combine EU countries with their parent region."""
    pairs: dict[tuple[date, str], dict[str, Decimal]] = {}
    for row in rows:
        group = pairs.setdefault((row.day, row.sector), {})
        if row.geography in group:
            raise AuditError("Duplicate reconciliation grain")
        group[row.geography] = row.mt_co2
    results = []
    with localcontext() as context:
        context.prec = 40
        for (day, sector), values in sorted(pairs.items()):
            if not set(PARTITION + ("WORLD",)) <= values.keys() or sector not in SECTORS:
                raise AuditError("Reconciliation requires WORLD and all eight disjoint regions")
            world = values["WORLD"]
            partition = precise_sum([values[g] for g in PARTITION])
            difference = world - partition
            tolerance = max(
                policy.absolute_tolerance, policy.relative_tolerance * max(world, partition)
            )
            results.append(
                Residual(
                    day,
                    sector,
                    world,
                    partition,
                    difference,
                    tolerance,
                    abs(difference) <= tolerance,
                )
            )
    return results
