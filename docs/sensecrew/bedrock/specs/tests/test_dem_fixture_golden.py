"""FAILING-FIRST golden tests for synthetic DEM fixtures (2320 (NEW-03)). Spec: ../dem-fixture-spec.md.
Names follow Loam GDD: dem_synthetic_<seed>.tif; M2 is the epoch pair 1002a (earlier) / 1002b (later).
Fixtures are SHA-256 exact (no float tolerance on bytes).
Fails with ImportError until sensegame.dem exists; golden hashes are PENDING and fail until
Bedrock-N records them (LEDGER entry + APPROVE) after the first reviewed generation.
"""
import hashlib, json, pathlib, struct
import pytest

from sensegame.dem import generate, write_geotiff, FIXTURES  # noqa: E402 (does not exist yet)

GOLDEN = pathlib.Path(__file__).with_name("dem_golden_sha256.json")
# key -> (seed, epoch)
CASES = [("1001", 1001, None), ("1002a", 1002, "a"), ("1002b", 1002, "b"), ("1003", 1003, None)]
SIZE, NODATA = 257, -9999.0


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


@pytest.mark.parametrize("key,seed,epoch", CASES)
def test_filename_is_synthetic(key, seed, epoch):
    assert FIXTURES[key] == f"fixtures/dem_synthetic_{key}.tif"
    assert key == f"{seed}{epoch or ''}"


def test_fixture_keys_match_gdd():
    assert sorted(FIXTURES) == ["1001", "1002a", "1002b", "1003"]


@pytest.mark.parametrize("key,seed,epoch", CASES)
def test_same_seed_byte_identical(tmp_path, key, seed, epoch):
    a, b = tmp_path / "a.tif", tmp_path / "b.tif"
    write_geotiff(generate(seed, epoch), a)
    write_geotiff(generate(seed, epoch), b)
    assert a.read_bytes() == b.read_bytes()


def test_different_seed_differs(tmp_path):
    a, b = tmp_path / "a.tif", tmp_path / "b.tif"
    write_geotiff(generate(1001), a)
    write_geotiff(generate(1003), b)
    assert sha(a) != sha(b)


def test_m2_epoch_required_and_only_for_1002():
    with pytest.raises(ValueError):
        generate(1002)
    with pytest.raises(ValueError):
        generate(1001, "a")
    with pytest.raises(ValueError):
        generate(1002, "c")


def test_m2_epoch_pair_semantics():
    """GDD node 1a: difference b - a; pits < 0, mounds > 0; same terrain elsewhere (v0: exactly 0)."""
    import numpy as np
    a = generate(1002, "a").astype("float64")
    b = generate(1002, "b").astype("float64")
    d = np.rint((b - a) * 1000.0).astype("int64")  # mm
    truth = json.loads((pathlib.Path(FIXTURES["1002b"]).parent / "dem_synthetic_1002_truth.json").read_text())
    assert len(truth["pits"]) == 3 and len(truth["mounds"]) == 3
    assert (d < 0).any() and (d > 0).any()
    assert int(d.min()) == -500 and int(d.max()) == 500
    feature = np.zeros(d.shape, bool)
    for f in truth["pits"] + truth["mounds"]:
        yy, xx = np.ogrid[:SIZE, :SIZE]
        feature |= (yy - f["row"]) ** 2 + (xx - f["col"]) ** 2 <= f["radius_px"] ** 2
    assert not d[~feature].any()


@pytest.mark.parametrize("key,seed,epoch", CASES)
def test_array_contract(key, seed, epoch):
    z = generate(seed, epoch)
    assert z.shape == (SIZE, SIZE) and str(z.dtype) == "float32"
    valid = z[z != NODATA]
    assert valid.size == SIZE * SIZE  # no nodata pixels in v0 fixtures
    assert 1000.0 <= float(valid.min()) and float(valid.max()) <= 1100.0
    import numpy as np
    mm = np.rint(z.astype("float64") * 1000.0).astype("int64")
    assert np.array_equal((mm / 1000.0).astype("float32"), z)  # heights quantised to integer mm


@pytest.mark.parametrize("key,seed,epoch", CASES)
def test_tiff_header_fixed(tmp_path, key, seed, epoch):
    p = tmp_path / "x.tif"
    write_geotiff(generate(seed, epoch), p)
    raw = p.read_bytes()
    assert raw[:4] == b"II*\x00" and struct.unpack("<I", raw[4:8])[0] == 8
    assert b"rasterio" not in raw and b"GDAL " not in raw  # no software/version strings
    (n,) = struct.unpack_from("<H", raw, 8)  # parse the single IFD at offset 8
    tags = [struct.unpack_from("<H", raw, 10 + 12 * i)[0] for i in range(n)]
    assert tags == sorted(tags)  # ascending tag order (TIFF 6.0)
    assert not {270, 305, 306} & set(tags)  # no ImageDescription / Software / DateTime
    assert 42113 in tags and 34735 in tags  # GDAL_NODATA + GeoKeyDirectory
    assert b"-9999" in raw  # GDAL_NODATA tag 42113 present


@pytest.mark.parametrize("key,seed,epoch", CASES)
def test_golden_sha256(tmp_path, key, seed, epoch):
    golden = json.loads(GOLDEN.read_text())  # PENDING: file created by Bedrock-N after review
    p = tmp_path / "x.tif"
    write_geotiff(generate(seed, epoch), p)
    assert golden[f"dem_synthetic_{key}.tif"] == sha(p)  # SHA-256 exact


def test_rasterio_reads_if_available(tmp_path):
    rasterio = pytest.importorskip("rasterio")  # optional cross-check only; BSD-3
    p = tmp_path / "x.tif"
    write_geotiff(generate(1001), p)
    with rasterio.open(p) as ds:
        assert ds.width == SIZE and ds.height == SIZE and ds.nodata == NODATA
        assert ds.transform.a == 1.0 and ds.transform.e == -1.0
