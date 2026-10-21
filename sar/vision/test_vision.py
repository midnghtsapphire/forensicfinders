"""Tests for vision (2110) on a tiny synthetic dataset generated here. No real imagery."""
import importlib.util, json, os, sys, tempfile, unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from vision import data, detect

HAS_CV2 = importlib.util.find_spec("cv2") is not None
HAS_TORCH = importlib.util.find_spec("torch") is not None and importlib.util.find_spec("torchvision") is not None


def make_dataset(root, sites=("siteA", "siteB"), flights=("f1", "f2"), frames=3, size=64):
    """Grey noise frames with one red 12x12 'item' each. Files at <site>/<flight>/<frame>.png."""
    rng = np.random.default_rng(0); images, anns, aid = [], [], 1
    for s in sites:
        for f in flights:
            os.makedirs(os.path.join(root, s, f), exist_ok=True)
            for k in range(frames):
                arr = rng.integers(90, 110, (size, size, 3), dtype=np.uint8)
                x, y = int(rng.integers(4, size - 16)), int(rng.integers(4, size - 16))
                arr[y:y + 12, x:x + 12] = [220, 30, 30]
                fn = f"{s}/{f}/{k}.png"; Image.fromarray(arr).save(os.path.join(root, fn))
                iid = len(images) + 1
                images.append({"id": iid, "file_name": fn, "width": size, "height": size})
                anns.append({"id": aid, "image_id": iid, "category_id": 7, "bbox": [x, y, 12, 12]}); aid += 1
    p = os.path.join(root, "coco.json")
    json.dump({"images": images, "annotations": anns, "categories": [{"id": 7, "name": "backpack"}]}, open(p, "w"))
    return p


class Loader(unittest.TestCase):
    def test_load_coco_groups_from_path(self):
        with tempfile.TemporaryDirectory() as d:
            ims, cats = data.load_coco(make_dataset(d))
            self.assertEqual(cats, {7: "backpack"}); self.assertEqual(len(ims), 12)
            self.assertEqual({(i["site"], i["flight"]) for i in ims}, {("siteA", "f1"), ("siteA", "f2"), ("siteB", "f1"), ("siteB", "f2")})
            self.assertTrue(all(len(i["boxes"]) == 1 and i["boxes"][0][2] == 12 for i in ims))

    def test_bad_annotation_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            json.dump({"images": [{"id": 1, "file_name": "a/b/c.png"}], "annotations": [{"id": 1, "image_id": 1, "category_id": 9, "bbox": [0, 0, 1, 1]}],
                       "categories": [{"id": 7, "name": "x"}]}, open(p, "w"))
            with self.assertRaises(ValueError): data.load_coco(p)


class Split(unittest.TestCase):
    def ims(self):
        return [{"site": s, "flight": f, "id": n} for n, (s, f) in enumerate([(s, f) for s in "ABCDE" for f in ("1", "2") for _ in range(4)])]

    def test_no_group_in_two_splits(self):
        sp = data.group_split(self.ims(), test_frac=0.3, val_frac=0.2, seed=3)
        g = {k: {(i["site"], i["flight"]) for i in v} for k, v in sp.items()}
        self.assertFalse(g["train"] & g["test"]); self.assertFalse(g["train"] & g["val"]); self.assertFalse(g["val"] & g["test"])
        self.assertEqual(sum(len(v) for v in sp.values()), 40)

    def test_deterministic_and_by_site(self):
        a = data.group_split(self.ims(), seed=1); b = data.group_split(self.ims(), seed=1)
        self.assertEqual([i["id"] for i in a["test"]], [i["id"] for i in b["test"]])
        s = data.group_split(self.ims(), by=("site",), seed=1)
        self.assertFalse({i["site"] for i in s["train"]} & {i["site"] for i in s["test"]})

    def test_one_group_refused(self):
        with self.assertRaises(ValueError): data.group_split([{"site": "A", "flight": "1"}])


@unittest.skipUnless(HAS_CV2, "opencv not installed")
class Template(unittest.TestCase):
    def test_finds_planted_patch(self):
        from vision.template import match
        rng = np.random.default_rng(1)
        img = rng.integers(0, 255, (100, 120, 3), dtype=np.uint8)
        tpl = img[40:55, 70:90].copy()
        hits = match(img, tpl, threshold=0.9)
        self.assertEqual(hits[0]["box"], [70, 40, 20, 15]); self.assertGreater(hits[0]["score"], 0.99)
        self.assertEqual(match(img, np.zeros((200, 200, 3), np.uint8)), [])

    def test_cli_writes_timeline_events(self):
        with tempfile.TemporaryDirectory() as d:
            rng = np.random.default_rng(2); img = rng.integers(0, 255, (80, 80, 3), dtype=np.uint8)
            Image.fromarray(img).save(os.path.join(d, "f.png")); Image.fromarray(img[10:30, 10:30]).save(os.path.join(d, "t.png"))
            meta = {"kind": "public_frame", "t_utc": "2026-10-21T12:00:00Z", "camera_id": "cam1", "media_path": os.path.join(d, "f.png")}
            json.dump(meta, open(os.path.join(d, "m.json"), "w"))
            w = detect.run("template", [meta], os.path.join(d, "det"), template=os.path.join(d, "t.png"), template_label="patch")
            self.assertEqual(len(w), 1)
            ev = json.load(open(w[0])); self.assertEqual(ev["kind"], "detector_candidate"); self.assertEqual(ev["review_status"], "unreviewed")
            from cameras import timeline
            tl = timeline.merge([timeline.from_camera_meta(meta), timeline.from_camera_meta(ev)])
            self.assertEqual([e["kind"] for e in tl], ["detector_candidate", "public_frame"])


class Off(unittest.TestCase):
    def test_none_is_default_and_does_nothing(self):
        self.assertEqual(detect.run("none", [{"media_path": "x"}], "/nonexistent"), [])
        self.assertEqual(detect.main(["whatever.json"]), 0)
        with self.assertRaises(ValueError): detect.run("yolo", [], "x")

    def test_recall_metric(self):
        from vision.frcnn import per_class_recall, iou_xywh
        self.assertAlmostEqual(iou_xywh([0, 0, 10, 10], [5, 0, 10, 10]), 50 / 150)
        r = per_class_recall([[{"box": [0, 0, 10, 10], "label_index": 1}], []],
                             [{"boxes": [[1, 1, 10, 10]], "labels": [7]}, {"boxes": [[0, 0, 5, 5]], "labels": [7]}], {7: 1}, {1: "backpack"})
        self.assertEqual(r, {"backpack": 0.5})


@unittest.skipUnless(HAS_TORCH, "torch/torchvision not installed")
class TrainSmoke(unittest.TestCase):
    def test_one_step_cpu(self):
        import torch
        from vision import frcnn
        torch.manual_seed(0)
        with tempfile.TemporaryDirectory() as d:
            ims, cats = data.load_coco(make_dataset(d, frames=1))
            m = frcnn.build_model(len(cats), pretrained=False)   # no download in tests
            r = frcnn.train(m, data.group_split(ims, seed=0)["train"], cats, max_steps=1, batch_size=1, log=lambda *_: None)
            self.assertEqual(r["steps"], 1); self.assertTrue(np.isfinite(r["last_loss"]))
            self.assertIsInstance(frcnn.predict(m, np.zeros((64, 64, 3), np.uint8), 0.0), list)


if __name__ == "__main__":
    unittest.main()
