# ADR 001: Preserve the licensed archived source

Status: accepted, 2026-10-07.

A byte-matched Kaggle version is available, while a current Carbon Monitor file differs materially and its relationship to the uploader vintage is unproven. Retain the existing CSV/PBIX, source receipt and exact checksums instead of silently replacing them or fabricating historical lineage. This keeps offline reproduction possible and exposes version uncertainty. The 8,283,578-byte existing CSV is the sole documented source-size exception; generated exports stay outside Git and retain ODbL/DbCL attribution.
