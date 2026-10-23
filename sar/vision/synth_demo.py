"""Synthetic-label demo (2120): train Faster R-CNN MobileNetV3 briefly on CPU, evaluate on held-out
backgrounds, compare with unsupervised RX / local-colour baselines.

    /home/box/venv-vision/bin/python -m vision.synth_demo --out /tmp/synth_demo --steps 300

SYNTHETIC ONLY - not field-validated. Writes metrics.json into --out (never commit generated data).
"""
import argparse, json, os, time

import numpy as np

from vision import anomaly, synth


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/synth_demo")
    ap.add_argument("--n-train", type=int, default=150)
    ap.add_argument("--n-test", type=int, default=60)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pretrained", action="store_true", help="COCO weights (downloads; check terms)")
    ap.add_argument("--img-size", type=int, default=384, help="detector input size (images are 192 px)")
    ap.add_argument("--skip-frcnn", action="store_true")
    a = ap.parse_args(argv)
    np.random.seed(a.seed)
    tr = synth.make_split(os.path.join(a.out, "train"), a.n_train, synth.TRAIN_BACKGROUNDS, a.seed)
    te = synth.make_split(os.path.join(a.out, "test"), a.n_test, synth.TEST_BACKGROUNDS, a.seed + 1000)
    res = {"label": "SYNTHETIC ONLY - not field-validated", "seed": a.seed,
           "train": {"n": len(tr), "backgrounds": synth.TRAIN_BACKGROUNDS, "objects": sum(len(r["boxes"]) for r in tr)},
           "test": {"n": len(te), "backgrounds": synth.TEST_BACKGROUNDS, "objects": sum(len(r["boxes"]) for r in te)}}
    from vision.frcnn import _load_image
    imgs = [_load_image(r["file"]) for r in te]
    for name, fn in (("rx_global", anomaly.rx_scores), ("local_colour", anomaly.local_scores)):
        t = time.time()
        preds = [anomaly.detect(fn(im)) for im in imgs]
        res[name] = {"AP50_class_agnostic": round(synth.ap50(preds, te), 4),
                     "recall_iou0.5": round(synth.recall_at(preds, te, 0.5, -1e9), 4),
                     "recall_iou0.3": round(synth.recall_at(preds, te, 0.3, -1e9), 4),
                     "dets_per_image": round(float(np.mean([len(p) for p in preds])), 2),
                     "sec": round(time.time() - t, 2)}
        print(name, res[name])
    if not a.skip_frcnn:
        import torch
        from vision import frcnn
        torch.manual_seed(a.seed); torch.set_num_threads(max(1, os.cpu_count() or 1))
        from torchvision.models.detection.anchor_utils import AnchorGenerator
        # Default MobileNetV3-FPN anchors start at 32 px; synthetic objects are 8-22 px, so use smaller
        # anchors (same 5 sizes x 3 ratios per location, so the pretrained RPN head still fits).
        anchors = AnchorGenerator(((8, 16, 32, 64, 128),) * 3, ((0.5, 1.0, 2.0),) * 3)
        m = frcnn.build_model(len(synth.CATS), pretrained=a.pretrained, min_size=a.img_size, max_size=a.img_size)
        m.rpn.anchor_generator = anchors
        t = time.time()
        tinfo = frcnn.train(m, tr, synth.CATS, epochs=1000, max_steps=a.steps, batch_size=4, lr=0.01,
                            log=lambda s: print(s) if s.split()[3].isdigit() and int(s.split()[3]) % 50 == 0 else None)
        ttrain = time.time() - t
        preds = [[{"box": q["box"], "score": q["score"], "label_index": q["label_index"]}
                  for q in frcnn.predict(m, im, 0.05)] for im in imgs]
        res["frcnn_mobilenetv3"] = {
            "pretrained_coco": a.pretrained, "img_size": a.img_size, "anchors": "8-128 px", "steps": tinfo["steps"], "last_loss": round(tinfo["last_loss"], 4),
            "train_sec": round(ttrain, 1),
            "AP50_class_agnostic": round(synth.ap50(preds, te), 4),
            "recall_iou0.5_score0.5": round(synth.recall_at(preds, te, 0.5, 0.5), 4),
            "per_class_recall_iou0.5_score0.5": frcnn.per_class_recall(
                [[q for q in p if q["score"] >= .5] for p in preds], te, {1: 1, 2: 2}, {1: "jacket", 2: "backpack"}),
        }
        print("frcnn", res["frcnn_mobilenetv3"])
    with open(os.path.join(a.out, "metrics.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    return res


if __name__ == "__main__":
    main()
