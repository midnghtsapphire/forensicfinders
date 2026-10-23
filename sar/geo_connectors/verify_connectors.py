#!/usr/bin/env python3
"""Live health check: one small real request per public endpoint (neutral bbox).
Writes a JSON report and prints status=PASS|FAIL. Exit 0 on PASS, 1 on FAIL.
Usage: python3 -m geo_connectors.verify_connectors [--out out/health.json] [--skip wayback]"""
import argparse, json, os, sys, time
from . import arcgis, dep3, stac, wayback

NEUTRAL = [-100.50, 41.00, -100.45, 41.05]
CHECKS = {
    "earth_search": lambda: len(stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["sentinel-2-l2a"], max_items=1, retries=2)) > 0,
    "cmr_lpcloud": lambda: len(stac.search(NEUTRAL, "2025-06-01/2025-06-30", ["HLSS30_2.0"], endpoint=stac.CMR_LPCLOUD, max_items=1, retries=2)) > 0,
    "usgs_3dep": lambda: dep3.sample_elevations([(-100.48, 41.02)], retries=2)[0]["elevation_m"] is not None,
    "wayback_cdx": lambda: len(wayback.query_cdx("example.com", 2006, 2007, limit=2, retries=2)) > 0,
    "arcgis": lambda: len(arcgis.query_layer("https://sampleserver6.arcgisonline.com/arcgis/rest/services/USA/MapServer/0", max_features=1, retries=2)["features"]) > 0,
}


def run(skip=()):
    res = {}
    for name, fn in CHECKS.items():
        if name in skip:
            res[name] = {"ok": None, "skipped": True}
            continue
        t = time.time()
        try:
            res[name] = {"ok": bool(fn())}
        except Exception as e:
            res[name] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}
        res[name]["seconds"] = round(time.time() - t, 2)
    status = "PASS" if all(v["ok"] is not False for v in res.values()) else "FAIL"
    return status, res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join("out", "health.json"))
    ap.add_argument("--skip", action="append", default=[], choices=list(CHECKS))
    a = ap.parse_args(argv)
    status, res = run(a.skip)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"status": status, "checks": res}, open(a.out, "w"), indent=2)
    print(json.dumps(res, indent=2))
    print(f"status={status}")
    gho = os.environ.get("GITHUB_OUTPUT")
    if gho:
        with open(gho, "a") as f:
            f.write(f"status={status}\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
