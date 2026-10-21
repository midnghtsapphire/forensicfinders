"""Getis-Ord Gi* (Ord & Getis 1995, Geographical Analysis 27(4):286-306, doi:10.1111/j.1538-4632.1995.tb00912.x)
on a raster with binary queen-contiguity weights including the cell itself (w_ii = 1).

  Gi* = (sum_j w_ij x_j - Xbar * W_i) / ( S * sqrt( (n*S1_i - W_i^2) / (n-1) ) )
  W_i = sum_j w_ij,  S1_i = sum_j w_ij^2,  S = sqrt(sum x^2/n - Xbar^2)

Edge cells use their actual (smaller) neighbourhoods, unlike the notebook version, which left edges at 0
and used n=9 everywhere with the wrong denominator. Verified against PySAL esda.G_Local(star=True) in tests."""
import numpy as np


def gi_star(grid):
    x = np.asarray(grid, dtype="float64")
    if x.ndim != 2 or x.size < 3:
        raise ValueError("need a 2-D grid with at least 3 cells")
    n = x.size
    xbar = x.mean()
    s = np.sqrt((x ** 2).mean() - xbar ** 2)
    out = np.zeros_like(x)
    if s == 0:
        return out
    R, C = x.shape
    for r in range(R):
        for c in range(C):
            win = x[max(0, r - 1):r + 2, max(0, c - 1):c + 2]
            w = win.size  # binary weights: W_i = S1_i = count
            num = win.sum() - xbar * w
            den = s * np.sqrt((n * w - w * w) / (n - 1))
            out[r, c] = num / den if den > 0 else 0.0  # window == whole grid: undefined, report 0
    return out
