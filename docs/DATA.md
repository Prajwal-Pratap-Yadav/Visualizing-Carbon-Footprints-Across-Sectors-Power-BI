# Data contract and provenance

The repository preserves a fixed, licensed daily emissions snapshot. It is an accounting review of that snapshot, not a current emissions inventory.

| Item | Verified observation | Evidence |
|---|---|---|
| Immediate publisher | Saloni Jhalani (`saloni1712`), *CO2 Emissions by Sectors*, Kaggle version 1 | [Download receipt](../data/source-receipt.json) |
| Publication vintage | Uploader update 2023-07-27; observations 2019-01-01–2023-05-31 | Receipt; [profile](../reports/reconciliation.json) |
| Original CSV | 8,283,578 bytes; SHA256 `5ea4c7e923a7efe42994b6933a62bd801f19f9338c6c29ab0d0825288538158d` | Public archive member byte-matched the original |
| Source database / contents license | ODbL 1.0 / DbCL 1.0 | [Attribution and reuse](../data/LICENSE.md) |
| Coverage | 135,408 records = 14 geography labels × 1,612 dates × 6 sectors | Exact, gap-free cross-product; no rows imputed or removed |
| Grain | Original geography label, UTC date, sector | DD/MM/YYYY date checked against source Unix timestamp |
| Gas | CO2 interpretation; no CO2e conversion | Dataset title and original report label |
| Physical unit | Interpreted MtCO2 for each daily sector observation | Original M label “In Mega Tons” and [Carbon Monitor display](https://carbonmonitor.org/); uploader-specific unit metadata absent |

The complete original CSV exceeds the normal 5 MB source-file limit. It is deliberately retained once, byte-for-byte, to support offline reproduction and license-compliant inspection of the existing project. No new oversized source file is introduced. Processed CSVs are generated locally, ignored by Git and included in the attributed evidence release.

## Source verification and vintage

[Public Kaggle metadata](https://www.kaggle.com/api/v1/datasets/view/saloni1712/co2-emissions) declared “Database: Open Database, Contents: Database Contents.” The [public download](https://www.kaggle.com/api/v1/datasets/download/saloni1712/co2-emissions) archive contains a single `dataset.csv` with the exact original checksum. The receipt records both archive and member hashes. This proves the immediate source match; it does not establish which historical Carbon Monitor release produced the uploaded values.

A separate [current-primary comparison](../reports/primary-current-comparison.json) used the public Carbon Monitor download. Of 96,720 overlapping geography/date/sector grains, 96,718 decimal values differed and two matched. The current file has different geography coverage and was **not substituted** for the archived source. Revisions mean a fresh primary download cannot be treated as a reconstruction of this vintage.

[Carbon Monitor methods](https://doi.org/10.1038/s41597-020-00708-7) concern fossil-fuel and cement CO2 activity estimates. That publication supports the methodological interpretation, not an independently verified lineage for this uploader snapshot. See [methodology](methodology.md) for territorial-like scope, LULUCF, aviation, shipping and uncertainty limits.

## Geography and schema

Eleven labels are countries with ISO3 keys. `EU27 & UK`, `ROW` and `WORLD` retain explicit composite/residual/world IDs. France, Germany, Italy, Spain and UK overlap the European composite. WORLD overlaps all constituent regions. Neither the source field name `country` nor the original dense rank makes all fourteen labels countries.

The candidate nonoverlapping partition is Brazil, China, EU27 & UK, India, Japan, Russia, US and ROW. Its sum is checked independently against each provided WORLD day/sector value. The report selects one geography at a time. The [generated dictionary](data-dictionary.md) defines normalized fields, exact MtCO2→tCO2 scaling and accounting flags. Population is absent, so per-capita results are unavailable.

## Validation and reuse

The importer requires the exact five-column schema, pinned source SHA256, supported labels, complete sector/date coverage, unique grain, UTC-midnight timestamp agreement and finite nonnegative bounded decimal values. Bad records fail the run with a readable error; none are silently discarded. The source receipt, licensing notes, accounting policy and raw checksum travel with the evidence archive. MIT applies to new code and the invented packaging fixture; the real source and derived databases retain ODbL/DbCL terms. Report figures and HTML attribute the source. Original PBIX bytes and existing MIT notice are preserved; embedded source data retains its own terms.
