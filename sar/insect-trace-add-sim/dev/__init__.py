"""Dev/test/prod environment scaffolding for insect-trace / taphonomy (2350 + 1010).

Dev and test: SYNTHETIC data only, schema-identical to prod.
Prod: connection info from environment variables only; never committed.
Real case rows live only in Secret's private table (location pending).
"""

__all__ = ["config", "db", "synthetic", "schema"]
