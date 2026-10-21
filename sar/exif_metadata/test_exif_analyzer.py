import os, tempfile, unittest
try:
    import piexif
    from PIL import Image
    from exif_analyzer import EXIFAnalyzer
except ImportError as e:  # optional deps
    raise unittest.SkipTest(f"piexif/Pillow not installed: {e}")

def jpeg(exif=None):
    f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False); f.close()
    img = Image.new("RGB", (8, 8))
    img.save(f.name, exif=piexif.dump(exif)) if exif else img.save(f.name)
    return f.name

class T(unittest.TestCase):
    def test_synthetic_metadata(self):
        p = jpeg({"0th": {piexif.ImageIFD.Make: b"TestCam", piexif.ImageIFD.Model: b"M1", piexif.ImageIFD.Software: b"GIMP 2.10"},
                  "Exif": {piexif.ExifIFD.DateTimeOriginal: b"2001:02:03 04:05:06"},
                  "GPS": {piexif.GPSIFD.GPSLatitudeRef: b"S", piexif.GPSIFD.GPSLatitude: ((1, 1), (30, 1), (0, 1)),
                          piexif.GPSIFD.GPSLongitudeRef: b"W", piexif.GPSIFD.GPSLongitude: ((2, 1), (0, 1), (0, 1))}})
        try: r = EXIFAnalyzer().analyze(p)
        finally: os.unlink(p)
        self.assertEqual(r["camera"]["make"], "TestCam")
        self.assertEqual(r["datetime"], "2001:02:03 04:05:06")
        self.assertAlmostEqual(r["location"]["latitude"], -1.5); self.assertAlmostEqual(r["location"]["longitude"], -2.0)
        self.assertIn("Edited with: GIMP 2.10", r["manipulation_indicators"])
    def test_no_exif_flags_missing(self):
        p = jpeg()
        try: r = EXIFAnalyzer().analyze(p)
        finally: os.unlink(p)
        self.assertIsNone(r.get("location"))
        self.assertIn("Missing camera information", r.get("manipulation_indicators", ["Missing camera information"]))

if __name__ == "__main__": unittest.main()
