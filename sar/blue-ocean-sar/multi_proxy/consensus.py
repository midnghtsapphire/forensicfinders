import numpy as np

def multiplicative_consensus(*layers: np.ndarray) -> np.ndarray:
    """Normalize each layer to [0,1] and multiply. Optional residual weighting later."""
    if not layers:
        raise ValueError("at least one layer required")
    out = np.ones_like(layers[0], dtype=float)
    for layer in layers:
        mn, mx = layer.min(), layer.max()
        if mx > mn:
            norm = (layer - mn) / (mx - mn)
        else:
            norm = np.zeros_like(layer)
        out *= norm
    return out
