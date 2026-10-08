"""Strict source extraction with independent grain and calendar coverage checks."""

import csv
import hashlib
import io
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from carbon_audit.domain import SECTORS, AuditError, Observation, Policy, decimal_value

FIELDS = ["country", "date", "sector", "value", "timestamp"]


def read_source(path: Path, policy: Policy) -> list[Observation]:
    """Retain every valid original record; reject silent gaps, aliases or unit guesses."""
    if path.stat().st_size > 12_000_000:
        raise AuditError("Source exceeds the documented 12 MB bound")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != policy.source_sha256:
        raise AuditError("Source checksum differs from the configured snapshot")
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")), strict=True)
        if reader.fieldnames != FIELDS:
            raise AuditError("CSV requires exactly the five ordered source headers")
        rows = []
        seen = set()
        for line, record in enumerate(reader, 2):
            if set(record) != set(FIELDS) or any(
                record[k] is None or not record[k].strip() for k in FIELDS
            ):
                raise AuditError(f"Blank or surplus fields at CSV line {line}")
            geography, sector = record["country"].strip(), record["sector"].strip()
            if geography not in policy.geographies or sector not in SECTORS:
                raise AuditError(f"Unknown geography/sector at CSV line {line}")
            if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", record["date"]):
                raise AuditError(f"Date must be DD/MM/YYYY at CSV line {line}")
            day = datetime.strptime(record["date"], "%d/%m/%Y").date()
            if not policy.first_day <= day <= policy.last_day:
                raise AuditError(f"Date outside configured period at CSV line {line}")
            expected = int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())
            if (
                not re.fullmatch(r"\d{10}", record["timestamp"])
                or int(record["timestamp"]) != expected
            ):
                raise AuditError(f"UTC-midnight timestamp mismatch at CSV line {line}")
            grain = (geography, day, sector)
            if grain in seen:
                raise AuditError(f"Duplicate canonical geography/date/sector at CSV line {line}")
            seen.add(grain)
            rows.append(Observation(geography, day, sector, decimal_value(record["value"].strip())))
            if len(rows) > 200_000:
                raise AuditError("Source exceeds 200,000 record bound")
        if not rows:
            raise AuditError("Source contains no observations")
        day = policy.first_day
        while day <= policy.last_day:
            for geography in policy.geographies:
                for sector in SECTORS:
                    if (geography, day, sector) not in seen:
                        raise AuditError(
                            f"Missing daily sector coverage: {geography}/{day}/{sector}"
                        )
            day += timedelta(days=1)
        return sorted(rows, key=lambda r: (r.day, r.geography_key, r.sector))
    except (UnicodeError, csv.Error, ValueError, OverflowError) as exc:
        if isinstance(exc, AuditError):
            raise
        raise AuditError(f"Invalid CSV: {exc}") from exc
