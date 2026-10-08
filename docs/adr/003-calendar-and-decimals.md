# ADR 003: Complete calendar windows and decimal accounting

Status: accepted, 2026-10-07.

The source ends in May 2023. Use complete-year YoY/CAGR only, calendar-matched YTD and seven-consecutive-day rolling windows. Preserve leap-year lengths and null zero-denominator results. Bounded decimal values and a 40-digit context avoid changing source arithmetic through binary-float import. Independent decimal and pandas checks provide separate evidence. Plotting/browser values may be rounded for display; the exported database is authoritative. Partial-year annualization and unconstrained float aggregation are rejected because they obscure source coverage and accounting precision.
