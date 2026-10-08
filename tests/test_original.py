"""Characterize the immutable inputs before any restructuring."""

import csv
import hashlib
import unittest
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OriginalTests(unittest.TestCase):
    def test_original_bytes(self):
        hashes = {
            "data/raw/emissions.csv": "5ea4c7e923a7efe42994b6933a62bd801f19f9338c6c29ab0d0825288538158d",
            "powerbi/original/carbon-footprints.pbix": "bc6d19180e2d18666c5feb0db2a4361ea30ef367aa27daa6a1a32905c5512f0b",
            "LICENSE": "4aae2fc6f9d5f27cf556519461713d508e8d3f91bc2df951ebcbeb18670f0726",
        }
        for name, checksum in hashes.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), checksum)

    def test_original_grain_calendar_and_timestamp(self):
        with (ROOT / "data/raw/emissions.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 135408)
        self.assertEqual(len({(r["country"], r["date"], r["sector"]) for r in rows}), len(rows))
        self.assertEqual(len({r["country"] for r in rows}), 14)
        self.assertEqual(len({r["sector"] for r in rows}), 6)
        self.assertEqual(len({r["date"] for r in rows}), 1612)
        for row in rows:
            self.assertEqual(
                datetime.fromtimestamp(int(row["timestamp"]), UTC).strftime("%d/%m/%Y"), row["date"]
            )


if __name__ == "__main__":
    unittest.main()
