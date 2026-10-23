"""Explicit no-data state: raised instead of returning synthetic/demo data."""


class NoDataError(RuntimeError):
    """No real input is available (missing credentials, file or upstream data)."""
