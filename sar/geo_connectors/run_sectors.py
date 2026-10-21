#!/usr/bin/env python3
"""Sector run: for each sector in a case config, search STAC scenes (cloud-filtered), compute mean
NDVI for the best before and after scenes (when rasterio is available), and sample the 3DEP elevation
at the sector centre. Everything it writes is computed from fetched data and recorded with its inputs.
No targets are typed in.
Usage: python3 -m geo_connectors.run_sectors --config case/example.config.yaml --out-dir out [--max-cloud-cover 20] [--no-cog]"""
import argparse, json, os, sys
from . import dep3, stac


def load_config(path):
    txt = open(path).read()
    try:
        import yaml
        return yaml.safe_load(txt)
    except ImportError:
        return json.loads(txt)


def _best(items):
    items = [i for i in items if i.get("cloud_cover") is not None]
    return min(items, key=lambda i: i["cloud_cover"]) if items else None


def run_sector(sec, img, max_cc, use_cog=True, **kw):
    import numpy as np
    q = {"eo:cloud_cover": {"lt": max_cc}}
    cols = img.get("collections", ["sentinel-2-l2a"])
    before = stac.search(sec["bbox"], img["before"], cols, max_items=20, query=q, **kw)
    after = stac.search(sec["bbox"], img["after"], cols, max_items=20, query=q, **kw)
    w, s, e, n = sec["bbox"]
    out = {"sector": sec["id"], "bbox": sec["bbox"], "max_cloud_cover": max_cc,
           "scenes_before": [i["id"] for i in before], "scenes_after": [i["id"] for i in after],
           "centre_elevation": dep3.sample_elevations([((w + e) / 2, (s + n) / 2)], **kw)}
    b0, b1 = _best(before), _best(after)
    if use_cog and b0 and b1:
        try:
            nd = [float(np.nanmean(stac.ndvi(stac.read_cog_window(x["assets"]["red"], sec["bbox"]),
                                             stac.read_cog_window(x["assets"]["nir"], sec["bbox"])))) for x in (b0, b1)]
            out["ndvi"] = {"before_scene": b0["id"], "after_scene": b1["id"], "mean_before": nd[0], "mean_after": nd[1], "delta": nd[1] - nd[0]}
        except Exception as ex:  # report, never invent
            out["ndvi"] = {"status": "no_data", "reason": f"{type(ex).__name__}: {ex}"[:300]}
    else:
        out["ndvi"] = {"status": "no_data", "reason": "no scene under the cloud limit" if use_cog else "COG step disabled"}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--max-cloud-cover", type=float)
    ap.add_argument("--no-cog", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    img = cfg["imagery"]
    mcc = a.max_cloud_cover if a.max_cloud_cover is not None else img.get("max_cloud_cover", 20)
    os.makedirs(a.out_dir, exist_ok=True)
    res = {"case_id": cfg.get("case_id"), "authority": cfg.get("authority"),
           "sectors": [run_sector(s, img, mcc, use_cog=not a.no_cog) for s in cfg["sectors"]]}
    p = os.path.join(a.out_dir, f"{cfg.get('case_id', 'run')}_sectors.json")
    json.dump(res, open(p, "w"), indent=2)
    print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
