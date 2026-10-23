"""OpenCV template-matching baseline (2110, --detector template). No training; rule-like."""
import numpy as np


def match(image, template, threshold=0.8, max_hits=20, label="template"):
    """Normalised cross-correlation. image/template: HxW or HxWx3 uint8 arrays.
    Returns [{box:[x,y,w,h], score, label}] after simple non-max suppression."""
    import cv2
    img = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    tpl = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY) if template.ndim == 3 else template
    th, tw = tpl.shape
    if th > img.shape[0] or tw > img.shape[1]:
        return []
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(res >= threshold)
    cand = sorted(zip(res[ys, xs], xs, ys), reverse=True)
    hits = []
    for s, x, y in cand:
        if all(abs(x - h["box"][0]) >= tw / 2 or abs(y - h["box"][1]) >= th / 2 for h in hits):
            hits.append({"box": [int(x), int(y), tw, th], "score": round(float(s), 4), "label": label})
        if len(hits) >= max_hits:
            break
    return hits
