import numpy as np

def spectral_angle(spectral: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Spectral Angle Mapper (radians). spectral: (H, W, B), reference: (B,)."""
    ref_norm = np.linalg.norm(reference)
    if ref_norm == 0:
        ref_norm = 1e-6
    angles = np.zeros(spectral.shape[:2])
    for r in range(spectral.shape[0]):
        for c in range(spectral.shape[1]):
            pix = spectral[r, c]
            pn = np.linalg.norm(pix)
            if pn == 0:
                pn = 1e-6
            cos = np.clip(np.dot(pix, reference) / (pn * ref_norm), -1.0, 1.0)
            angles[r, c] = np.arccos(cos)
    return angles
