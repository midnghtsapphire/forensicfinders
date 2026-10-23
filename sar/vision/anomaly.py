"""Unsupervised colour-anomaly baselines (no training labels): global RX and local colour-statistics.

RX (Reed & Yu 1990, doi:10.1109/29.60107; "Reed-Xiaoli" after Xiaoli Yu): per-pixel Mahalanobis distance from the image's
background mean/covariance. The local variant uses a box-filtered mean/variance window (diagonal
covariance) so it adapts to terrain changes. Own implementation from the published description.
Detections = connected components above a robust threshold, scored by peak distance.
"""
import numpy as np


def rx_scores(img, robust=True):
    x = img.reshape(-1, img.shape[-1]).astype(float)
    if robust:  # estimate background stats from the central 95% of pixels to limit target contamination
        d0 = np.linalg.norm(x - np.median(x, 0), axis=1)
        bg = x[d0 <= np.quantile(d0, .95)]
    else:
        bg = x
    mu, cov = bg.mean(0), np.cov(bg.T) + 1e-6 * np.eye(x.shape[1])
    inv = np.linalg.inv(cov)
    d = x - mu
    return np.sqrt(np.einsum("ij,jk,ik->i", d, inv, d)).reshape(img.shape[:2])


def local_scores(img, win=31):
    from scipy import ndimage
    x = img.astype(float)
    mu = ndimage.uniform_filter(x, (win, win, 1))
    var = np.maximum(ndimage.uniform_filter(x * x, (win, win, 1)) - mu * mu, 1.0)
    return np.sqrt((((x - mu) ** 2) / var).sum(-1))


def detect(scores, k=6.0, min_area=12, max_area=2000):
    """Threshold at median + k*MAD, label connected components, return [{'box','score'}]."""
    from scipy import ndimage
    med = np.median(scores); mad = np.median(np.abs(scores - med)) * 1.4826 + 1e-9
    m = scores > med + k * mad
    m = ndimage.binary_closing(m, iterations=1)
    lab, n = ndimage.label(m)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None:
            continue
        area = int((lab[sl] == i).sum())
        if not (min_area <= area <= max_area):
            continue
        y, x = sl
        peak = (float(scores[sl][lab[sl] == i].max()) - med) / mad   # robust z, comparable across images
        out.append({"box": [x.start, y.start, x.stop - x.start, y.stop - y.start], "score": peak})
    return out
