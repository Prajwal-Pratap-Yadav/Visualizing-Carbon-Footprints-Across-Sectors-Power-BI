"""Check documentation contracts, immutable originals, exact versions and source bounds."""

import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote

from carbon_audit import __version__

ROOT = Path(__file__).resolve().parents[1]
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
paths = {ROOT / p for p in tracked if p}
paths.update(p for p in (ROOT / "docs").rglob("*") if p.is_file())
paths.update(ROOT / p for p in ["README.md", "docs/EVIDENCE.md", "docs/RELEASE.md"])
problems = []
source_receipt = json.loads((ROOT / "data/source-receipt.json").read_text())
source_hash = source_receipt["files"][0]["sha256"]
for path in sorted(paths):
    if not path.is_file():
        problems.append(f"Missing source file: {path.relative_to(ROOT)}")
        continue
    if path.stat().st_size > 5_000_000:
        allowed = (
            path == ROOT / "data/raw/emissions.csv"
            and path.stat().st_size == 8283578
            and hashlib.sha256(path.read_bytes()).hexdigest() == source_hash
        )
        if not allowed:
            problems.append(f"Undocumented oversized file: {path.relative_to(ROOT)}")
    if path.suffix != ".md" or path.name == "README-original.md":
        continue
    for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text()):
        target = link.split("#", 1)[0].split(" ", 1)[0]
        if not target or re.match(r"[a-z]+:", target):
            continue
        dest = (path.parent / unquote(target)).resolve()
        if not dest.is_relative_to(ROOT) or not dest.exists():
            problems.append(f"Broken local link in {path.relative_to(ROOT)}: {link}")
required = [
    "Why this matters",
    "Quickstart",
    "Features",
    "Architecture",
    "Design decisions",
    "Results and limitations",
    "Repo map",
    "Development",
    "Roadmap",
    "License, data and citation",
]
readme = (ROOT / "README.md").read_text()
if re.findall(r"^## (.+)$", readme, re.MULTILINE) != required:
    problems.append("README sections differ from fixed portfolio order")
if len(readme.splitlines()[2].split()) > 18:
    problems.append("Value proposition exceeds 18 words")
badges = re.findall(r"https://img\.shields\.io/[^)]+", readme)
if len(badges) != 4 or any(
    "style=flat-square" not in b or "labelColor=0b1220" not in b for b in badges
):
    problems.append("Four ordered portfolio-style badges required")
metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
if (
    metadata["version"] != __version__
    or f"## [{__version__}]" not in (ROOT / "CHANGELOG.md").read_text()
    or f"version: {__version__}" not in (ROOT / "CITATION.cff").read_text()
):
    problems.append("Package/changelog/citation versions differ")
for row in json.loads((ROOT / "reports/baseline-files.json").read_text()):
    path = {
        "Datasets.csv": "data/raw/emissions.csv",
        "Visualizing Carbon Footprints.pbix": "powerbi/original/carbon-footprints.pbix",
        "README.md": "powerbi/original/README-original.md",
        "LICENSE": "LICENSE",
    }[row["path"]]
    if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != row["sha256"]:
        problems.append(f"Original bytes changed: {path}")
fields = [
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
for field in fields:
    if f"`{field}`" not in (ROOT / "docs/data-dictionary.md").read_text():
        problems.append(f"Dictionary misses {field}")
for name in [
    "reports/reconciliation.json",
    "reports/model/catalog.json",
    "data/source-receipt.json",
    "reports/insights.json",
]:
    json.loads((ROOT / name).read_text())
if problems:
    raise SystemExit("\n".join(problems))
print(
    "Fixed README order, local links, source-size exception, original hashes and schema/version metadata pass."
)
