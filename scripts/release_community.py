"""Assign the three existing scoped issues to the next audited-report milestone."""

import json
import os
import urllib.request

REPOSITORY = "Prajwal-Pratap-Yadav/Visualizing-Carbon-Footprints-Across-Sectors-Power-BI"


def write_ok():
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or os.environ.get("GITHUB_REF") not in {
        "refs/heads/main",
        "refs/heads/portfolio-overhaul",
    }:
        raise SystemExit(
            "Community mutation is restricted to the named repository and reviewed branches"
        )


def api(method, endpoint, payload=None):
    if method != "GET":
        write_ok()
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/{endpoint}",
        data=None if payload is None else json.dumps(payload).encode(),
        method=method,
        headers={
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


write_ok()
title = "Next verified companion (0.2.0)"
milestones = api("GET", "milestones?state=all&per_page=100")
milestone = next((m for m in milestones if m["title"] == title), None)
if milestone is None:
    milestone = api(
        "POST",
        "milestones",
        {
            "title": title,
            "description": "Desktop/DAX output confirmation, source-vintage/unit/transport lineage and a reviewed PBIP companion. These are unverified roadmap items.",
        },
    )
if milestone["number"] != 1:
    raise SystemExit("Milestone ID differs from README link; update the reviewed documentation")
labels = api("GET", "labels?per_page=100")
existing = {label["name"] for label in labels}
for name, color, description in [
    ("desktop-validation", "38bdf8", "Requires genuine Desktop and DAX output evidence"),
    ("source-provenance", "fbbf24", "Primary lineage and accounting definition evidence"),
    ("model-review", "a78bfa", "Reviewed companion model and data-join contract"),
]:
    if name not in existing:
        api("POST", "labels", {"name": name, "color": color, "description": description})
for number, label in [(1, "desktop-validation"), (2, "source-provenance"), (3, "model-review")]:
    issue = api("GET", f"issues/{number}")
    if "pull_request" in issue:
        raise SystemExit("Roadmap ID resolved to a pull request")
    if (issue.get("milestone") or {}).get("number") != milestone["number"]:
        api("PATCH", f"issues/{number}", {"milestone": milestone["number"]})
    current_labels = {item["name"] for item in issue.get("labels", [])}
    if label not in current_labels:
        api("POST", f"issues/{number}/labels", {"labels": [label]})
print("Roadmap milestone #1 verified for issues #1, #2 and #3.")
