import numpy as np

def topp_dielectric(soil_moisture: np.ndarray) -> np.ndarray:
    """Topp et al. cubic empirical model for real dielectric from volumetric moisture."""
    m = np.clip(soil_moisture, 0.0, 0.6)
    return 3.03 + 9.3 * m + 146.0 * m**2 - 76.7 * m**3
