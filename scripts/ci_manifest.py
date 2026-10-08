"""Record real CPU job environment, test counts and reproduction source."""

import importlib.metadata
import json
import os
import platform
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(".")
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
if os.environ.get("GITHUB_SHA", sha) != sha:
    raise SystemExit("Checked-out source differs from the workflow SHA")
coverage = json.loads((root / "reports/local/coverage.json").read_text())["totals"]
junit = ET.parse(root / "reports/local/tests.xml").getroot()
suites = list(junit.iter("testsuite"))
reported = {
    name: sum(int(s.attrib.get(name, 0)) for s in suites)
    for name in ["tests", "failures", "errors", "skipped"]
}
cases = list(junit.iter("testcase"))
summary = {
    "tests": len(cases),
    "failures": sum(c.find("failure") is not None for c in cases),
    "errors": sum(c.find("error") is not None for c in cases),
    "skipped": sum(c.find("skipped") is not None for c in cases),
}
if summary["failures"] or summary["errors"] or reported["failures"] or reported["errors"]:
    raise SystemExit("Refuse to record a failed test suite as passing")
payload = {
    "source_git_sha": sha,
    "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
    "workflow_run_url": (
        f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        if os.environ.get("GITHUB_RUN_ID") and os.environ.get("GITHUB_REPOSITORY")
        else None
    ),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "cpu_count": os.cpu_count(),
    "versions": {
        p: importlib.metadata.version(p)
        for p in ["pytest", "pytest-cov", "ruff", "black", "mypy", "matplotlib", "nbformat"]
    },
    "tests": summary,
    "junit_suite_reported": reported,
    "test_count_method": "Executed testcase entries; suite counts also include unittest subtest pass events in the pinned pytest version.",
    "coverage_percent": coverage["percent_covered"],
    "coverage_scope": "src/carbon_audit; subprocess entry guard not covered; scripts/model/rendering excluded",
    "source_data_sha256": json.loads((root / "configs/policy.json").read_text())["source_sha256"],
    "scope": "Real CPU audit/unit/end-to-end/reproduction run; no Power BI UI, refresh or DAX engine output validated.",
}
(root / "reports/local/ci-manifest.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(payload, indent=2))
