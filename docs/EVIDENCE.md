# Evidence register

## Baseline and immutable inputs

Original main `47e91e43e6731faef9a148f60e9504e94f563d62` had three historical commits and four files, with no tests, build or CI. [Baseline inventory](../reports/baseline-files.json) records exact original sizes/hashes. CSV, PBIX, historical README and MIT notice are preserved byte-for-byte; existing Git history is retained. The source is 135,408 geography/date/sector records, not person-level data.

A fresh public Kaggle v1 archive member matched the original CSV checksum. [Receipt](../data/source-receipt.json) records the immediate creator, declared ODbL/DbCL terms and archive/member hashes. Primary historical Carbon Monitor release lineage and uploader-specific unit metadata remain qualified. [DATA](DATA.md) distinguishes the verified immediate source from the methodological interpretation.

## Measured accounting and report evidence

The [run manifest](../reports/run_manifest.json) comes from an actual clean published-source checkout at `f607ead031adca4673e8d71e26b311908ca7b273`, generated on 2026-10-07. Initial worktree state is empty. It records Linux x86_64, Python 3.12.14, matplotlib 3.11.2, nbformat 5.11.1, source/policy checksums and generated artifact hashes. Source numeric profiles, dictionary, insights, HTML and figure reproduce; timestamps and notebook environment metadata may change on re-execution.

| Claim | Measured value | Command / method | Source, date and environment | Artifact |
|---|---|---|---|---|
| Retained source coverage | 135,408 / 135,408 rows; 14 labels, 6 sectors, 1,612 dates | `make run`; exact validated grain | Run-manifest source; 2026-10-07; Linux/Python 3.12.14 | [Reconciliation](../reports/reconciliation.json) |
| Unsafe combined scope | 2.054054692198218266… × WORLD | `make reproduce`; whole-snapshot ratio | Same measured source/environment | Profile; `geography-trap` notebook cell |
| Independent spatial consistency | 9,672 checks, all pass; maximum gap 0.000136 interpreted MtCO2 | WORLD versus eight-region partition with declared tolerance | Same measured source/environment | Profile; generated complete residual CSV |
| WORLD complete 2022 | 36,119.462025 interpreted MtCO2; +1.722091751282524785…% YoY | Adjacent complete calendar sums | Same measured source/environment | [Analysis](../reports/analysis.json); `complete-years` cell |
| WORLD Jan–May 2023 | 15,113.988959 interpreted MtCO2; +0.341402943499572511…% matched YoY | January 1–May 31 in both years, 151 observed 2023 days | Same measured source/environment | [Insights](../reports/insights.json); `matched-ytd` cell |
| Actual notebook execution | Six ordinary-Python code cells with captured stdout | `scripts/execute_notebook.py`; no Jupyter kernel claimed | Same measured source/environment | [Executed notebook](../notebooks/01_accounting.ipynb) |
| Original report structure | Four tables; three calculated tables; thirteen calculated columns; zero explicit measures; four pages/25 native visuals | Read-only `make setup-inspect inspect` | Clean published source; Python 3.12.14, PBIXRay 0.15.5/pandas 3.0.6/numpy 2.5.3 | [Catalog](../reports/model/catalog.json) |
| Source/cache agreement | 135,408 matching grains; maximum per-value float difference 1.1102230246251565e-16 | Decoded cached table versus independently read source | Same inspection environment | [Cross-checks](../reports/model/arithmetic-crosschecks.json) |
| Independent reproduction | All raw/export grains, residuals, annual/monthly/YTD sums and shares pass | Separate 50-digit Decimal calculation | Clean published source; 2026-10-07; Python 3.12.14 | `scripts/check_reproduction.py`; exports/profile/report-data hashes |
| Independent pandas arithmetic | Annual totals, complete YoY, sector shares, CAGR and latest strict seven-day mean within explicit tolerances | `scripts/check_model.py` | Same clean source and recorded inspector versions | Cross-check JSON; no DAX output claim |
| Real figure and offline report | Decimal-backed figures and one-geography calendar views | `make reproduce` | Clean source/environment in manifest | [Hero](assets/carbon-review.png), [HTML](assets/carbon-report.html), [report data](../reports/report-data.json) |

Every insight identifies a named notebook cell. Spatial tolerance verifies internal arithmetic, not physical estimate accuracy. Six-sector totals are derived; no independent all-sector inventory total is supplied.

## Hosted CPU and browser verification

[Actual workflow 37652948498](https://github.com/Prajwal-Pratap-Yadav/Visualizing-Carbon-Footprints-Across-Sectors-Power-BI/actions/runs/37652948498) verified source `f607ead031adca4673e8d71e26b311908ca7b273`. Python 3.11.16 and 3.12.14, original-model inspection, full-history/advisory security, browser checks and roadmap community setup all passed. The release job correctly skipped on the development branch. [Python 3.11 manifest](../reports/ci/python-3.11.16.json) and [Python 3.12 manifest](../reports/ci/python-3.12.14.json) contain the actual printed workflow environment/source/test evidence.

Both Python jobs passed **48 executable testcase entries**, zero failures/errors/skips and **98.2905982905983% statement coverage** over `src/carbon_audit`. Scripts, binary decoder, browser rendering and Power BI are excluded. The pinned pytest JUnit suite reports 51 pass events because it also counts three successful unittest subtests; the manifests preserve both quantities rather than calling those events 51 separate collected tests. The first inspection job exposed a missing generated-analysis prerequisite. `make inspect` now depends on the real audit, and both a clean-target check and hosted inspection passed.

The hosted browser job passed **six actual Playwright tests**, covering all **70 geography/year combinations**, explicit matched-YTD labels, the accessible numeric table, widths **1440/768/390** without page overflow, no serious/critical axe violations at those widths and no HTTP resource requests. These are scoped checks, not full WCAG certification. [Browser summary](../reports/browser/summary.json) records source/run, observed counts, downloaded artifact ID and archive checksum.

The actual hosted artifact was downloaded and its API digest verified. Every image matches the hash in its [capture receipt](../reports/browser/capture-manifest.json); the HTML hash also matches clean-source reproduction. [Desktop](assets/report-desktop.png), [YTD](assets/report-ytd.png) and [mobile](assets/report-mobile.png) views were captured with Playwright 1.63.0 / pinned Chromium 153.0.8010.12 on Linux x64 and visually reviewed. The receipt distinguishes the earlier report-generation SHA from the actual published capture source. They are **companion-report captures, not Power BI exports**. Earlier local checks used reviewed portable Chromium 153.0.8010.0 after official downloads failed locally; the committed captures and summary now use the downloaded hosted evidence.

## Clean-checkout and presentation gates

The exact three README operations, with explicit development-branch selection before merge, completed in **40.734 seconds** at published source `b651546983c3832728aad784e3f7cf5c8e0c9317`. This used new empty pip/uv directories and disabled pip caching; network/proxy/OS caches were uncontrolled. Final Git status was clean. Full developer setup, lint, types, 48-case tests, audit, reproduction, docs, build, read-only inspection and security subsequently passed from that fresh checkout. Developer-phase download caches may be reused; no timed developer-install claim is made.

The checkout was advanced to published `f607ead…`, generated files were reset to the preserved committed versions, local generated outputs were cleaned, and `make inspect` regenerated its prerequisite and passed. Reproduction then started with an actually clean tree and produced the committed manifest/notebook evidence. A standalone built wheel was installed in an isolated environment; its **108 invented records / 12 passing spatial checks** validate packaging only, not emissions science.

[Quality gates](../reports/quality-gates.json) identify scoped self-review rather than an external recruiter or stranger study. Actual GitHub review verified all four badge images and the real 2400px hero loaded; the nine-node Mermaid diagram rendered. Main's CI badge may remain cached until main runs. The title, real-data visual, source caption, evidence paths, structure and granular owner history were reviewed for quick comprehension. No independent human timing experiment is claimed.

Roadmap issues #1–#3 are assigned to milestone #1, Next verified companion (0.2.0). The current PR head must complete its checks before an owner-authored non-squash merge. The guarded main workflow then creates an annotated owner tag on exact main and publishes attributed artifacts/checksums. Default-main quickstart and actual release download/source/install verification are recorded after publication in the execution ledger; no pre-publication download verification is claimed here.

## Security and remaining scope

Checksum-verified gitleaks 8.30.1 found no secrets in reviewed original/overhaul history. The historical CSV/PBIX object was separately reviewed through source rows, archive/layout, import/security metadata and cached tables. No credential or person-level record was found. Text scanners do not decode compressed models. The original owner's local import path remains in the unchanged binary and is redacted in the text catalog. Pinned Python/Node advisory checks passed; these are scoped controls, not security certification.

Desktop refresh/render, proposed DAX engine outputs, primary historical release lineage, uploader-specific unit metadata and transport allocation remain unverified. No CO2e, population/per-capita, current-inventory, scientific-accuracy or causal result is supplied. Repository description/topics/social administration remains outside the installed connection's mutation capabilities. [Methodology](methodology.md), [DATA](DATA.md) and scoped roadmap items explain the practical limits.
