# Carbon accounting audit: review guide

Review geography and time-window accounting before interpreting totals in a historical reporting artifact.

## Follow the implementation

| Start here | File | What to inspect |
| --- | --- | --- |
| Domain model | [src/carbon_audit/domain.py](../src/carbon_audit/domain.py) | Explicit accounting entities and window definitions. |
| Reconciliation | [src/carbon_audit/reconcile.py](../src/carbon_audit/reconcile.py) | How aggregates reconcile and double counting becomes visible. |
| Analytics | [src/carbon_audit/analytics.py](../src/carbon_audit/analytics.py) | Computed measures and reporting inputs. |
| Accounting tests | [tests/test_accounting.py](../tests/test_accounting.py) | Arithmetic and domain invariants. |
| Original preservation | [tests/test_original.py](../tests/test_original.py) | Archived source checks. |
| Case study | [docs/CASE_STUDY.md](../docs/CASE_STUDY.md) | Measured findings and interpretation boundaries. |

## Run the checks

Run from the repository root after the setup described in the [README](../README.md). Review fixtures and recorded evidence before starting any full experiment.

```bash
make setup-dev
make test docs
make reproduce
```

## Interpret the evidence

Findings concern the checked-in historical dataset and reporting assumptions. They do not form a current emissions inventory. The Python/HTML companion is independently inspectable; it does not prove that a Power BI Desktop refresh was executed.

The linked reports retain their original experiment dates and protocols. A new passing CI run verifies its named checks; it does not silently refresh historical measurements.

## Discuss the design

- Which aggregates overlap geographically or temporally?
- Why should reconciliation failures remain visible instead of being hidden by a dashboard filter?
