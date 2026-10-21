"""Tests for the 2120 synthetic-label demo pieces (synthetic only)."""
import os, tempfile, unittest
import numpy as np

from vision import synth

try:
    import scipy  # noqa: F401
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False
try:
    import torch, torchvision  # noqa: F401
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
try:
    import PIL  # noqa: F401
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


class Compose(unittest.TestCase):
    def test_boxes_exact_and_seeded(self):
        r1, r2 = np.random.default_rng(3), np.random.default_rng(3)
        a, b = synth.background("grass", r1), synth.background("grass", r2)
        ba, la = synth.composite(a, r1, 3); bb, lb = synth.composite(b, r2, 3)
        self.assertEqual((ba, la), (bb, lb)); self.assertTrue(np.array_equal(a, b))
        for x, y, w, h in ba:
            self.assertTrue(0 <= x and 0 <= y and x + w <= 192 and y + h <= 192 and w >= 4 and h >= 4)

    def test_box_is_tight_to_pasted_pixels(self):
        rng = np.random.default_rng(0)
        img = np.zeros((192, 192, 3)); before = img.copy()
        boxes, _ = synth.composite(img, rng, 1)
        changed = np.nonzero((img != before).any(-1))
        x, y, w, h = boxes[0]
        self.assertEqual((changed[1].min(), changed[0].min(), changed[1].max() + 1, changed[0].max() + 1), (x, y, x + w, y + h))

    def test_train_test_backgrounds_disjoint(self):
        self.assertFalse(set(synth.TRAIN_BACKGROUNDS) & set(synth.TEST_BACKGROUNDS))

    @unittest.skipUnless(HAVE_PIL, "Pillow missing")
    def test_make_split_writes_coco(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            recs = synth.make_split(d, 4, synth.TEST_BACKGROUNDS, seed=1)
            coco = json.load(open(os.path.join(d, "annotations.json")))
            self.assertEqual(len(coco["images"]), 4)
            self.assertEqual(len(coco["annotations"]), sum(len(r["boxes"]) for r in recs))
            self.assertIn("SYNTHETIC", coco["info"]["description"])

    def test_ap_perfect_and_empty(self):
        g = [{"boxes": [[0, 0, 10, 10]]}]
        self.assertAlmostEqual(synth.ap50([[{"box": [0, 0, 10, 10], "score": .9}]], g), 1.0)
        self.assertEqual(synth.ap50([[]], g), 0.0)


@unittest.skipUnless(HAVE_SCIPY, "scipy missing")
class Anomaly(unittest.TestCase):
    def test_rx_finds_orange_patch(self):
        from vision import anomaly
        rng = np.random.default_rng(0)
        img = synth.background("forest", rng)
        img[50:64, 80:92] = (240, 120, 20)
        dets = anomaly.detect(anomaly.rx_scores(img))
        from vision.frcnn import iou_xywh
        self.assertTrue(any(iou_xywh(d["box"], [80, 50, 12, 14]) > .5 for d in dets))


@unittest.skipUnless(HAS_TORCH and HAVE_PIL and HAVE_SCIPY, "torch/torchvision not installed")
class DemoSmoke(unittest.TestCase):
    def test_demo_runs_two_steps(self):
        from vision import synth_demo
        with tempfile.TemporaryDirectory() as d:
            r = synth_demo.main(["--out", d, "--n-train", "4", "--n-test", "2", "--steps", "2", "--img-size", "192"])
            self.assertEqual(r["frcnn_mobilenetv3"]["steps"], 2)
            self.assertIn("SYNTHETIC", r["label"])


if __name__ == "__main__":
    unittest.main()
