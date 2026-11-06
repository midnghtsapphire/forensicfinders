"""Single source of truth for table and column names.

MySQL 8 DDL (ddl_mysql8.sql) and SQLite DDL (ddl_sqlite.sql) MUST expose
the same table names and the same column names (types may differ).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

EXPECTED_TABLES: Tuple[str, ...] = (
    "cases_anonymized",
    "sites",
    "temperature_series",
    "insect_observations",
    "add_estimates",
    "pmi_estimates",
    "audit_log",
)

TABLE_COLUMNS: Dict[str, Tuple[str, ...]] = {
    "cases_anonymized": (
        "case_id",
        "env",
        "anon_code",
        "is_synthetic",
        "location_label",
        "jurisdiction_code",
        "opened_at",
        "notes_public",
        "created_at",
    ),
    "sites": (
        "site_id",
        "case_id",
        "env",
        "site_code",
        "lat_round",
        "lon_round",
        "elevation_m",
        "habitat",
        "created_at",
    ),
    "temperature_series": (
        "temp_id",
        "site_id",
        "env",
        "observed_at",
        "temp_c",
        "source",
        "created_at",
    ),
    "insect_observations": (
        "obs_id",
        "site_id",
        "env",
        "taxon",
        "stage",
        "length_mm",
        "collected_at",
        "collector_role",
        "created_at",
    ),
    "add_estimates": (
        "add_id",
        "site_id",
        "env",
        "method",
        "add_value",
        "base_temp_c",
        "confidence",
        "model_ref",
        "created_at",
    ),
    "pmi_estimates": (
        "pmi_id",
        "site_id",
        "env",
        "add_id",
        "pmi_hours_low",
        "pmi_hours_high",
        "confidence",
        "model_ref",
        "created_at",
    ),
    "audit_log": (
        "audit_id",
        "env",
        "actor",
        "action",
        "entity_table",
        "entity_id",
        "detail",
        "created_at",
    ),
}


def schema_fingerprint() -> List[str]:
    out: List[str] = []
    for table in EXPECTED_TABLES:
        for col in TABLE_COLUMNS[table]:
            out.append(f"{table}.{col}")
    return out
