"""Audit a fixed source snapshot without network, Power BI or plotting dependencies."""

import argparse
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any

from carbon_audit.domain import AuditError, Policy
from carbon_audit.export import export
from carbon_audit.extract import read_source
from carbon_audit.reconcile import reconcile


def audit(source: Path, policy_path: Path, output: Path) -> dict[str, Any]:
    policy = Policy.load(policy_path)
    rows = read_source(source, policy)
    return export(rows, reconcile(rows, policy), policy, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw/emissions.csv"))
    parser.add_argument("--policy", type=Path, default=Path("configs/policy.json"))
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--demo", action="store_true", help="Use invented MIT fixture; packaging test only"
    )
    options = parser.parse_args()
    if options.demo:
        options.input = Path(str(files("carbon_audit").joinpath("fixtures/emissions.csv")))
        options.policy = Path(str(files("carbon_audit").joinpath("fixtures/policy.json")))
    try:
        report = audit(options.input, options.policy, options.output)
    except (AuditError, OSError) as exc:
        print(f"Audit rejected: {exc}", file=sys.stderr)
        return 2
    print(
        f"{report['retained_rows']} rows retained; {report['spatial_passes']}/{report['spatial_checks']} spatial checks pass."
    )
    print(
        f"Outputs: {options.output}; six-sector totals are derived, source vintage/units/scope limits apply."
    )
    return 1 if report["spatial_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
