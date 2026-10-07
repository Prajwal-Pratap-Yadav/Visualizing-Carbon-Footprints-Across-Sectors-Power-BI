"""Explicit geography scopes, bounded policy and decimal observations."""

import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

SECTORS = (
    "Domestic Aviation",
    "Ground Transport",
    "Industry",
    "International Aviation",
    "Power",
    "Residential",
)
GEOGRAPHIES = {
    "Brazil": ("BRA", "country"),
    "China": ("CHN", "country"),
    "France": ("FRA", "country"),
    "Germany": ("DEU", "country"),
    "India": ("IND", "country"),
    "Italy": ("ITA", "country"),
    "Japan": ("JPN", "country"),
    "Russia": ("RUS", "country"),
    "Spain": ("ESP", "country"),
    "UK": ("GBR", "country"),
    "US": ("USA", "country"),
    "EU27 & UK": ("EU27_UK", "composite_region"),
    "ROW": ("ROW", "residual_region"),
    "WORLD": ("WORLD", "world"),
}
PARTITION = ("Brazil", "China", "EU27 & UK", "India", "Japan", "Russia", "US", "ROW")
DATABASE_LICENSE = "ODbL-1.0; contents DbCL-1.0"


class AuditError(ValueError):
    """A rejected source or policy with a concise, actionable reason."""


def decimal_value(text: str) -> Decimal:
    """Reject nonfinite/extreme input before arithmetic or export can overflow."""
    if len(text) > 40:
        raise AuditError("Numeric text exceeds 40 characters")
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise AuditError("Invalid decimal value") from exc
    if not value.is_finite() or value < 0:
        raise AuditError("Emissions must be finite and nonnegative")
    if len(value.as_tuple().digits) > 20:
        raise AuditError("Numeric value exceeds 20 significant digits")
    if value and not -12 <= value.adjusted() <= 12:
        raise AuditError("Numeric magnitude outside supported bounds")
    return value if value else Decimal(0)


def precise_sum(values: list[Decimal]) -> Decimal:
    """Forty digits cover the bounded source magnitudes and maximum row count."""
    with localcontext() as context:
        context.prec = 40
        return sum(values, Decimal(0))


@dataclass(frozen=True, slots=True)
class Observation:
    geography: str
    day: date
    sector: str
    mt_co2: Decimal

    @property
    def geography_key(self) -> str:
        return GEOGRAPHIES[self.geography][0]

    @property
    def geography_scope(self) -> str:
        return GEOGRAPHIES[self.geography][1]

    @property
    def t_co2(self) -> Decimal:
        return self.mt_co2.scaleb(6)


@dataclass(frozen=True)
class Policy:
    source_sha256: str
    first_day: date
    last_day: date
    geographies: tuple[str, ...]
    absolute_tolerance: Decimal
    relative_tolerance: Decimal
    data_creator: str
    data_license: str
    source_url: str
    synthetic: bool

    @classmethod
    def load(cls, path: Path) -> "Policy":
        """Validate configuration instead of guessing units, geography or period."""
        try:
            raw: Any = json.loads(path.read_text(encoding="utf-8"))
            keys = {
                "source_sha256",
                "first_day",
                "last_day",
                "geographies",
                "absolute_tolerance",
                "relative_tolerance",
                "data_creator",
                "data_license",
                "source_url",
                "synthetic",
                "source_unit",
                "gas",
                "accounting_basis",
                "unit_provenance",
                "lulucf",
                "gwp_horizon",
                "shipping_treatment",
            }
            if not isinstance(raw, dict) or set(raw) != keys:
                raise AuditError("Policy keys differ from the supported schema")
            if raw["source_unit"] != "MtCO2" or raw["gas"] != "CO2":
                raise AuditError("Only the documented MtCO2/CO2 interpretation is supported")
            if raw["accounting_basis"] != "source_activity_estimate":
                raise AuditError("Consumption-based or other accounting basis is unsupported")
            if raw["gwp_horizon"] != "not_applicable_CO2":
                raise AuditError("GWP conversion is not applicable to this CO2-only source")
            if raw["lulucf"] != "outside_referenced_fossil_cement_scope":
                raise AuditError("LULUCF is outside the referenced source scope")
            if raw["shipping_treatment"] != "not_separately_present_unverified":
                raise AuditError("Separate shipping coverage cannot be inferred")
            strings = [k for k in keys if k not in {"geographies", "synthetic"}]
            if any(not isinstance(raw[k], str) or not raw[k].strip() for k in strings):
                raise AuditError("Policy string fields must be nonempty strings")
            if not re.fullmatch(r"[0-9a-f]{64}", raw["source_sha256"]):
                raise AuditError("Policy requires an exact lowercase SHA256")
            if not isinstance(raw["synthetic"], bool):
                raise AuditError("synthetic must be a boolean")
            first, last = date.fromisoformat(raw["first_day"]), date.fromisoformat(raw["last_day"])
            if first > last or (last - first).days > 3660:
                raise AuditError("Unsupported date range")
            geographies = raw["geographies"]
            if not isinstance(geographies, list) or any(
                not isinstance(g, str) or g not in GEOGRAPHIES for g in geographies
            ):
                raise AuditError("Unknown geography labels in policy")
            if len(set(geographies)) != len(geographies) or not set(PARTITION + ("WORLD",)) <= set(
                geographies
            ):
                raise AuditError("Policy must include WORLD and the unique eight-region partition")
            absolute = decimal_value(raw["absolute_tolerance"])
            relative = decimal_value(raw["relative_tolerance"])
            if absolute > Decimal("0.001") or relative > Decimal("0.0001"):
                raise AuditError("Reconciliation tolerance exceeds the audit limit")
            return cls(
                raw["source_sha256"],
                first,
                last,
                tuple(geographies),
                absolute,
                relative,
                raw["data_creator"],
                raw["data_license"],
                raw["source_url"],
                raw["synthetic"],
            )
        except (OSError, ValueError, TypeError, KeyError) as exc:
            if isinstance(exc, AuditError):
                raise
            raise AuditError(f"Invalid policy: {exc}") from exc
