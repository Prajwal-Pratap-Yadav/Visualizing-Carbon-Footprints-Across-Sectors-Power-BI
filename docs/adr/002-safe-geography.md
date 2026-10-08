# ADR 002: Single-geography analytics and a separate disjoint partition

Status: accepted, 2026-10-07.

The original label field mixes eleven countries with WORLD, EU27 & UK and ROW. A combined sum double-counts coverage. Use explicit country ISO3/aggregate IDs, one geography per analytic view, and a dedicated eight-region export reconciled to the independently provided WORLD series. Retain all source records rather than deleting aggregates. This trades unrestricted multiselect for totals whose accounting scope can be explained and reviewed.
