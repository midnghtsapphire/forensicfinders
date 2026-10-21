"""Synthetic-label SAR imagery: procedurally generated backgrounds + composited jacket/backpack-coloured
shapes with exact boxes (2120 prototype).

Everything is generated from a seed: no photographs, no third-party or copyrighted data. Results on
this data are SYNTHETIC ONLY and say nothing about field performance; the next step is real labelled
aerial SAR imagery (see HANDOFF §13 for HERIDAL / SARD and their licence status).

Records match vision.data.load_coco output: {"file", "boxes" [[x,y,w,h]], "labels" [cat id], "background"}.
"""
import json
import os

import numpy as np

CATS = {1: "jacket", 2: "backpack"}
# Train and held-out test use DIFFERENT background families, so the test measures transfer to new terrain.
TRAIN_BACKGROUNDS = ("grass", "forest", "scrub")
TEST_BACKGROUNDS = ("rock", "sand")
_BG = {  # base RGB, blotch RGB, texture contrast
    "grass": ((86, 120, 52), (60, 95, 40), 18),
    "forest": ((38, 62, 34), (20, 40, 22), 22),
    "scrub": ((120, 110, 70), (80, 95, 55), 20),
    "rock": ((128, 124, 118), (95, 92, 90), 24),
    "sand": ((190, 170, 130), (165, 145, 110), 14),
}
JACKET_COLOURS = [(220, 40, 30), (240, 120, 20), (240, 220, 40), (30, 70, 200), (200, 30, 140),
                  (70, 85, 50), (110, 90, 65)]   # last two: olive / brown, low-contrast cases
BACKPACK_COLOURS = [(30, 30, 35), (20, 110, 170), (200, 60, 30), (90, 40, 140), (10, 140, 90),
                    (60, 70, 45), (120, 100, 75)]


def _noise(rng, h, w, scale):
    """Smooth value noise: random coarse grid, bilinear upsample."""
    gh, gw = max(2, h // scale + 2), max(2, w // scale + 2)
    g = rng.random((gh, gw))
    yy = np.linspace(0, gh - 1.001, h); xx = np.linspace(0, gw - 1.001, w)
    y0, x0 = yy.astype(int), xx.astype(int)
    fy, fx = (yy - y0)[:, None], (xx - x0)[None, :]
    a, b = g[y0][:, x0], g[y0][:, x0 + 1]
    c, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def background(kind, rng, h=192, w=192):
    base, blotch, contrast = _BG[kind]
    m = _noise(rng, h, w, 24)[..., None]
    img = np.array(base) * (1 - m) + np.array(blotch) * m
    img = img + (_noise(rng, h, w, 6)[..., None] - 0.5) * contrast + rng.normal(0, 4, (h, w, 3))
    return img


def _shape_mask(rng, ph, pw, kind):
    yy, xx = np.mgrid[0:ph, 0:pw]
    if kind == "jacket":   # ellipse-ish torso, sometimes with "arms"
        m = ((yy - ph / 2 + .5) / (ph / 2)) ** 2 + ((xx - pw / 2 + .5) / (pw / 2)) ** 2 <= 1
        if rng.random() < .5:
            m |= (np.abs(yy - ph * .35) < ph * .12)
    else:                  # rounded rectangle with a darker strap band
        r = min(ph, pw) * .25
        cy, cx = np.clip(yy, r, ph - 1 - r), np.clip(xx, r, pw - 1 - r)
        m = (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
    return m


def composite(img, rng, n_objects, min_size=8, max_size=22):
    """Paste shaded shapes; returns boxes [x,y,w,h] (tight to the mask) and category ids."""
    h, w = img.shape[:2]
    boxes, labels, occ = [], [], np.zeros((h, w), bool)
    for _ in range(n_objects * 5):
        if len(boxes) == n_objects:
            break
        cid = int(rng.integers(1, 3))
        kind = CATS[cid]
        ph, pw = (int(v) for v in rng.integers(min_size, max_size + 1, 2))
        if kind == "backpack":
            ph, pw = max(min_size, int(ph * .7)), max(min_size, int(pw * .7))
        y, x = int(rng.integers(0, h - ph)), int(rng.integers(0, w - pw))
        if occ[max(0, y - 2):y + ph + 2, max(0, x - 2):x + pw + 2].any():
            continue
        m = _shape_mask(rng, ph, pw, kind)
        col = np.array((JACKET_COLOURS if cid == 1 else BACKPACK_COLOURS)[rng.integers(0, 7)], float)
        shade = 0.75 + 0.35 * np.linspace(1, 0, ph)[:, None] * np.ones((1, pw))   # top-lit
        patch = col * shade[..., None] + rng.normal(0, 6, (ph, pw, 3))
        if kind == "backpack":
            patch[:, pw // 3: pw // 3 + max(1, pw // 6)] *= 0.6
        region = img[y:y + ph, x:x + pw]
        region[m] = patch[m]
        occ[y:y + ph, x:x + pw] |= m
        ys, xs = np.nonzero(m)
        boxes.append([x + int(xs.min()), y + int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)])
        labels.append(cid)
    return boxes, labels


def distractors(img, rng, n):
    """Unlabelled clutter that a colour-anomaly detector will fire on: flower clusters, bright rocks,
    shadows, a pale trail stripe. Not objects of interest, so no boxes."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(n):
        t = rng.integers(0, 4)
        cy, cx, r = rng.integers(0, h), rng.integers(0, w), rng.integers(3, 10)
        m = (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
        if t == 0:    # flower cluster: speckled red/yellow/white dots inside a disc
            col = np.array([(230, 50, 60), (240, 220, 60), (240, 240, 240)][rng.integers(0, 3)], float)
            m &= rng.random((h, w)) < .35
            img[m] = col
        elif t == 1:  # pale boulder
            img[m] = img[m] * .3 + np.array((210, 205, 195)) * .7
        elif t == 2:  # shadow
            img[m] *= .45
        else:         # trail stripe
            a = rng.uniform(0, np.pi)
            d = np.abs((xx - cx) * np.sin(a) - (yy - cy) * np.cos(a))
            img[d < 2] = img[d < 2] * .4 + np.array((200, 185, 150)) * .6


def make_split(out_dir, n, backgrounds, seed, size=192, max_objects=4, n_distractors=4):
    """Write n PNGs + annotations.json (COCO-style) and return records."""
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(seed)
    recs, coco = [], {"images": [], "annotations": [], "categories": [{"id": k, "name": v} for k, v in CATS.items()],
                      "info": {"description": "SYNTHETIC ONLY, generated by sar/vision/synth.py", "seed": seed}}
    for i in range(n):
        kind = backgrounds[i % len(backgrounds)]
        img = background(kind, rng, size, size)
        distractors(img, rng, int(rng.integers(0, n_distractors + 1)))
        boxes, labels = composite(img, rng, int(rng.integers(1, max_objects + 1)))
        f = os.path.join(out_dir, f"{kind}_{i:04d}.png")
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f)
        recs.append({"file": f, "boxes": boxes, "labels": labels, "background": kind})
        coco["images"].append({"id": i, "file_name": os.path.basename(f), "width": size, "height": size})
        for b, c in zip(boxes, labels):
            coco["annotations"].append({"id": len(coco["annotations"]), "image_id": i, "category_id": c,
                                        "bbox": b, "area": b[2] * b[3], "iscrowd": 0})
    with open(os.path.join(out_dir, "annotations.json"), "w") as fh:
        json.dump(coco, fh)
    return recs


def ap50(preds, gts, iou_thr=0.5):
    """Class-agnostic VOC-style AP (all-point interpolation) at iou_thr. Own code; preds use {'box','score'}."""
    from vision.frcnn import iou_xywh
    dets, npos = [], sum(len(g["boxes"]) for g in gts)
    for i, p in enumerate(preds):
        dets += [(q["score"], i, q["box"]) for q in p]
    dets.sort(key=lambda d: -d[0])
    used = [set() for _ in gts]
    tp = []
    for s, i, b in dets:
        best, bj = 0, -1
        for j, g in enumerate(gts[i]["boxes"]):
            o = iou_xywh(b, g)
            if o > best and j not in used[i]:
                best, bj = o, j
        if best >= iou_thr:
            used[i].add(bj); tp.append(1)
        else:
            tp.append(0)
    if not npos:
        return 0.0
    tp = np.array(tp, float); fp = 1 - tp
    rec = np.cumsum(tp) / npos; prec = np.cumsum(tp) / np.maximum(np.cumsum(tp) + np.cumsum(fp), 1e-9)
    mrec = np.concatenate([[0], rec, [1]]); mpre = np.concatenate([[0], prec, [0]])
    for k in range(len(mpre) - 2, -1, -1):
        mpre[k] = max(mpre[k], mpre[k + 1])
    idx = np.nonzero(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def recall_at(preds, gts, iou_thr=0.5, score_thr=0.5):
    from vision.frcnn import iou_xywh
    hit = tot = 0
    for p, g in zip(preds, gts):
        ps = [q for q in p if q["score"] >= score_thr]
        used = set()
        for b in g["boxes"]:
            tot += 1
            for k, q in enumerate(ps):
                if k not in used and iou_xywh(b, q["box"]) >= iou_thr:
                    used.add(k); hit += 1; break
    return hit / tot if tot else 0.0
