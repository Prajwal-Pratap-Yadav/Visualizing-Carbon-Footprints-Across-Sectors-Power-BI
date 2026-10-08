# Generated data dictionary

Generated from the normalized export contract. All fields are required, finite and nonblank; nulls/gaps/duplicates are rejected rather than imputed. Original timestamp is validated before export. Input/units/licence: [DATA](DATA.md).

| Column | Type | Unit / meaning | Method / source |
|---|---|---|---|
| `geography` | string | source label | Original country column; includes countries/composites/aggregates |
| `geography_key` | string | ISO3 or explicit aggregate ID | Country keys are ISO3; composite IDs are never relabelled as countries |
| `geography_scope` | enum | category | country / composite_region / residual_region / world |
| `date` | ISO date | UTC day | Parsed DD/MM/YYYY and checked against original Unix UTC-midnight timestamp |
| `sector` | enum | source taxonomy | One of the six original sector labels |
| `value_mt_co2` | decimal | interpreted MtCO2 per source day | Original decimal value retained; unit metadata caveat in DATA.md |
| `value_t_co2` | decimal | interpreted tCO2 per source day | Exact multiplication by 1,000,000; not a new physical estimate |
| `gas` | constant | CO2 | No CO2e or multi-gas conversion |
| `accounting_basis` | constant | source_activity_estimate | Territorial-like activity interpretation, not consumption accounting |
| `unit_interpretation` | constant | documented_MtCO2_interpretation | Corroborated interpretation; uploader-specific unit metadata absent |
