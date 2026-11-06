"""Canonical table specs + DDL loaders for MySQL 8 and SQLite."""

from .tables import EXPECTED_TABLES, TABLE_COLUMNS, schema_fingerprint

__all__ = ["EXPECTED_TABLES", "TABLE_COLUMNS", "schema_fingerprint"]
