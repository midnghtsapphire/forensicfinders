import numpy as np
from dielectric import topp_dielectric
from twi import calculate_twi
from consensus import multiplicative_consensus
from nnls_unmix import constrained_nnls_unmix

def test_topp():
    m = np.array([0.0, 0.2, 0.4])
    d = topp_dielectric(m)
    assert d[0] == 3.03
    assert d[1] > d[0]

def test_twi_shape():
    dem = np.random.rand(10, 10) * 10
    twi = calculate_twi(dem)
    assert twi.shape == dem.shape

def test_nnls_and_consensus():
    em = {
        "a": np.array([1.0, 0.0]),
        "b": np.array([0.0, 1.0]),
    }
    spec = np.zeros((2, 2, 2))
    spec[0, 0] = em["a"]
    fracs, rms = constrained_nnls_unmix(spec, em)
    assert fracs["a"][0, 0] > 0.9
    assert rms[0, 0] < 1e-6
    cons = multiplicative_consensus(fracs["a"], 1.0 - rms)
    assert cons.shape == (2, 2)
