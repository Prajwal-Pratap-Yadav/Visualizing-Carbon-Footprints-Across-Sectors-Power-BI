# Source and report lineage

```mermaid
flowchart TD
  K["Kaggle v1 archive"] --> H["Pinned CSV and source receipt"]
  H --> V["Schema, units and calendar checks"]
  V --> E["Retained normalized records"]
  E --> R["WORLD versus eight-region audit"]
  E --> A["Single-geography calendar analysis"]
  R --> P["Notebook and companion report"]
  A --> P
  H --> B["Preserved original PBIX"]
  B --> C["Read-only model and cache catalog"]
  C --> P
  classDef input fill:#0b1220,stroke:#38bdf8,color:#e2e8f0;
  classDef proc fill:#111827,stroke:#a78bfa,color:#e2e8f0;
  classDef store fill:#111827,stroke:#34d399,color:#e2e8f0;
  classDef out fill:#0b1220,stroke:#fbbf24,color:#e2e8f0;
  class K,H input;
  class V,R,A,C proc;
  class E,B store;
  class P out;
```

The immediate source archive is verified by a byte match. Original PBIX and CSV are preserved independently of the companion calculation. No new measures or visuals are installed in that binary. [Original model catalog](../reports/model/catalog.json) records its expressions and visual bindings; [cached cross-checks](../reports/model/arithmetic-crosschecks.json) compare decoded records with the source. Generated dictionaries, profiles, notebook stdout, figure and self-contained HTML report retain source attribution. Each run records source Git SHA, worktree state, package versions and output hashes in [run_manifest.json](../reports/run_manifest.json).

The current primary-source comparison is a separate diagnostic, not an input substitution. The report uses the fixed archived source even when current values differ. Proposed companion DAX requires a separate reviewed model; Desktop refresh/render and DAX evaluation remain manual.
