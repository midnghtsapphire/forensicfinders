import numpy as np

def calculate_twi(dem: np.ndarray, cell_size: float = 1.0) -> np.ndarray:
    """Topographic Wetness Index = ln(a / tan(β))."""
    rows, cols = dem.shape
    dy, dx = np.gradient(dem, cell_size)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    slope = np.maximum(slope, 1e-4)
    # Simple D8-style accumulation (placeholder; replace with richer flow later)
    flow_acc = np.ones_like(dem) * cell_size
    order = np.argsort(dem.ravel())[::-1]
    for idx in order:
        r, c = divmod(idx, cols)
        min_elev = dem[r, c]
        target = None
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and dem[nr, nc] < min_elev:
                    min_elev = dem[nr, nc]
                    target = (nr, nc)
        if target:
            nr, nc = target
            flow_acc[nr, nc] += flow_acc[r, c]
    return np.log(flow_acc / np.tan(slope))
