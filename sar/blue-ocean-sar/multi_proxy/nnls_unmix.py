import numpy as np
from scipy.optimize import nnls

def constrained_nnls_unmix(spectral: np.ndarray, endmembers: dict) -> tuple[dict, np.ndarray]:
    """FCLS-style unmixing (non-negative + sum-to-one) + RMS residual.
    spectral: (H, W, B); endmembers: {name: (B,) array}
    Returns fractions dict + rms error map.
    """
    keys = list(endmembers.keys())
    A = np.stack([endmembers[k] for k in keys], axis=1)
    H, W, B = spectral.shape
    fracs = {k: np.zeros((H, W)) for k in keys}
    rms = np.zeros((H, W))
    for r in range(H):
        for c in range(W):
            x, _ = nnls(A, spectral[r, c])
            s = x.sum()
            if s > 0:
                x /= s
            for i, k in enumerate(keys):
                fracs[k][r, c] = x[i]
            recon = A @ x
            rms[r, c] = np.sqrt(np.mean((spectral[r, c] - recon) ** 2))
    return fracs, rms
