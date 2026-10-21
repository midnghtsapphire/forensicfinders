"""
Public records ingestion engine: pluggable connectors only.

This replaces the original hard-coded sample dossier. The engine holds no data
of its own. Each section is filled only by a connector you register, and an
empty section reports {"status": "no_data"} instead of inventing values.

Built-in connector: "census", which calls the U.S. Census Geocoder
(opendata/census.py) for a public address and returns tract and block group.

Person-level sources (voter files, vital records, genealogy) need lawful
authority (FCRA permissible purpose, state voter-file limits, site terms), so
none is built in. Register your own callable and record the authority it runs
under, e.g. engine.register("voter_records", fn, authority="agency MOU #...").
"""
import datetime
import json

SECTIONS = ("census_data", "neighbors_proximity", "voter_records", "vital_statistics", "genealogical_records")


class PublicRecordsDataEngine:
    def __init__(self, clock=None):
        self._connectors = {}
        self._clock = clock or (lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def register(self, section, fn, authority):
        if section not in SECTIONS:
            raise ValueError(f"unknown section {section!r}; one of {SECTIONS}")
        if not authority or not str(authority).strip():
            raise ValueError("authority is required: record the lawful basis for this lookup")
        self._connectors[section] = (fn, str(authority).strip())
        return self

    def compile_all(self, subject):
        out = {"generated_at": self._clock(), "subject": subject, "sections": {}}
        for s in SECTIONS:
            if s not in self._connectors:
                out["sections"][s] = {"status": "no_data", "reason": "no connector registered"}
                continue
            fn, auth = self._connectors[s]
            try:
                data = fn(subject)
            except Exception as e:  # report, never fabricate
                out["sections"][s] = {"status": "error", "authority": auth, "error": f"{type(e).__name__}: {e}"}
                continue
            out["sections"][s] = {"status": "ok" if data else "no_data", "authority": auth, "data": data or None}
        return out


def census_connector(opener=None):
    """Connector backed by the public Census Geocoder. subject needs an 'address' key."""
    import os, sys
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opendata")
    if d not in sys.path:
        sys.path.insert(0, d)
    import census

    def fn(subject):
        addr = subject.get("address")
        if not addr:
            return None
        kw = {"opener": opener} if opener else {}
        return census.geocode_address(addr, **kw)
    return fn


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit("usage: public_records_engine.py '<public address>'")
    e = PublicRecordsDataEngine().register("census_data", census_connector(), authority="public Census Geocoder")
    print(json.dumps(e.compile_all({"address": sys.argv[1]}), indent=2))
