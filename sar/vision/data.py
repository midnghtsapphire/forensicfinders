"""Dataset loading and leak-free splits for the optional detector (2110).

Loads COCO JSON (CVAT and Label Studio both export COCO). Site and flight come from each image's
"site"/"flight" fields, or are parsed from the file path `<site>/<flight>/<frame>.jpg`.
Splits are made by (site, flight) group, never by frame, so neighbouring frames can't leak.
"""
import hashlib, json, os, random
from pathlib import Path


def _group_from_path(fn):
    parts = Path(fn).parts
    return (parts[-3], parts[-2]) if len(parts) >= 3 else ("unknown", "unknown")


def load_coco(path, image_root=None):
    """Return (images, categories). images: [{id, file, width, height, site, flight, boxes:[[x,y,w,h]], labels:[cat_id]}]."""
    d = json.load(open(path))
    root = Path(image_root) if image_root else Path(path).parent
    cats = {c["id"]: c["name"] for c in d.get("categories", [])}
    if not cats:
        raise ValueError("COCO file has no categories")
    imgs = {}
    for im in d["images"]:
        site, flight = im.get("site"), im.get("flight")
        if not (site and flight):
            site, flight = _group_from_path(im["file_name"])
        imgs[im["id"]] = {"id": im["id"], "file": str(root / im["file_name"]), "width": im.get("width"),
                          "height": im.get("height"), "site": str(site), "flight": str(flight), "boxes": [], "labels": []}
    for a in d.get("annotations", []):
        if a["image_id"] not in imgs or a["category_id"] not in cats:
            raise ValueError(f"annotation {a.get('id')} points at a missing image or category")
        x, y, w, h = a["bbox"]
        if w <= 0 or h <= 0:
            continue
        imgs[a["image_id"]]["boxes"].append([float(x), float(y), float(w), float(h)])
        imgs[a["image_id"]]["labels"].append(int(a["category_id"]))
    return list(imgs.values()), cats


def group_split(images, test_frac=0.2, val_frac=0.0, seed=0, by=("site", "flight")):
    """Split by group key (default site+flight). Deterministic for a given seed. Returns dict of lists."""
    groups = sorted({tuple(im[k] for k in by) for im in images})
    if len(groups) < 2:
        raise ValueError("need at least 2 site/flight groups to make a leak-free split")
    rng = random.Random(seed); rng.shuffle(groups)
    n_test = max(1, round(len(groups) * test_frac))
    n_val = round(len(groups) * val_frac)
    test_g, val_g = set(groups[:n_test]), set(groups[n_test:n_test + n_val])
    out = {"train": [], "val": [], "test": []}
    for im in images:
        g = tuple(im[k] for k in by)
        out["test" if g in test_g else "val" if g in val_g else "train"].append(im)
    return out


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
