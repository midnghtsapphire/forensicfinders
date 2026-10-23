"""Optional detection CLI (2110). OFF by default: --detector none does nothing.

Reads 1911/1912 frame metadata JSON (needs media_path, t_utc, camera_id), runs a detector on each frame and
writes one 1913-compatible metadata JSON per candidate (kind "detector_candidate"). Merge them with
`python3 -m cameras.timeline merge <frames>/*.json out/detections/*.json`.
Every candidate is labelled for HUMAN REVIEW. It is never an identification.

  python3 -m vision.detect --detector none     out/frames/*.json
  python3 -m vision.detect --detector template --template item.png out/frames/*.json
  python3 -m vision.detect --detector frcnn --weights model.pt --classes classes.json out/frames/*.json
  python3 -m vision.detect train --coco labels.json --out model.pt [--epochs 10]
  python3 -m vision.detect eval  --coco labels.json --weights model.pt
"""
import argparse, glob, json, os, sys

DETECTORS = ("none", "template", "frcnn")


def _read_rgb(path):
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"))


def candidates_to_events(meta, hits, detector, model_id):
    from .data import sha256_file
    sha = meta.get("sha256") or (sha256_file(meta["media_path"]) if os.path.exists(meta["media_path"]) else None)
    out = []
    for n, h in enumerate(hits):
        out.append({"kind": "detector_candidate", "t_utc": meta.get("t_utc"),
                    "camera_id": f"{meta.get('camera_id', 'unknown')}#det{n}",
                    "camera_name": f"REVIEW: {h['label']} ({detector}, score {h['score']})",
                    "lat": meta.get("lat"), "lon": meta.get("lon"), "media_path": meta["media_path"], "sha256": sha,
                    "event_id": f"{model_id}:{h['box']}", "detector": detector, "model_id": model_id,
                    "box_xywh": h["box"], "score": h["score"], "label": h["label"], "review_status": "unreviewed"})
    return out


def run(detector, metas, out_dir, template=None, template_label="template", threshold=None,
        weights=None, classes=None):
    if detector not in DETECTORS:
        raise ValueError(f"--detector must be one of {DETECTORS}")
    if detector == "none":
        return []
    os.makedirs(out_dir, exist_ok=True)
    if detector == "template":
        if not template:
            raise ValueError("--template is required for --detector template")
        from .template import match
        tpl = _read_rgb(template); model_id = f"template:{os.path.basename(template)}"
        fn = lambda arr: match(arr, tpl, threshold or 0.8, label=template_label)
    else:
        import torch
        from . import frcnn
        names = json.load(open(classes))                       # ["backpack", "jacket", ...] in label-index order
        model = frcnn.build_model(len(names), pretrained=False)
        model.load_state_dict(torch.load(weights, map_location="cpu")); model_id = f"frcnn:{os.path.basename(weights)}"
        fn = lambda arr: [dict(h, label=names[h["label_index"] - 1]) for h in frcnn.predict(model, arr, threshold or 0.5)]
    written = []
    for m in metas:
        if not m.get("media_path") or not os.path.exists(m["media_path"]):
            continue
        for i, ev in enumerate(candidates_to_events(m, fn(_read_rgb(m["media_path"])), detector, model_id)):
            p = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(m['media_path']))[0]}_det{i}.json")
            json.dump(ev, open(p, "w"), indent=1); written.append(p)
    return written


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("train", "eval"):
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--coco", required=True)
        ap.add_argument("--images"); ap.add_argument("--weights"); ap.add_argument("--out", default="out/vision/model.pt")
        ap.add_argument("--epochs", type=int, default=10); ap.add_argument("--max-steps", type=int)
        ap.add_argument("--test-frac", type=float, default=0.2); ap.add_argument("--seed", type=int, default=0)
        a = ap.parse_args(argv)
        import torch
        from . import data, frcnn
        ims, cats = data.load_coco(a.coco, a.images)
        sp = data.group_split(ims, a.test_frac, seed=a.seed)
        print(f"groups: train {len(sp['train'])} imgs, test {len(sp['test'])} imgs (split by site/flight)")
        if a.cmd == "train":
            m = frcnn.build_model(len(cats))
            print(frcnn.train(m, sp["train"], cats, a.epochs, a.max_steps))
            os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
            torch.save(m.state_dict(), a.out)
            json.dump([cats[k] for k in sorted(cats)], open(os.path.splitext(a.out)[0] + ".classes.json", "w"))
            print("saved", a.out)
        else:
            m = frcnn.build_model(len(cats), pretrained=False); m.load_state_dict(torch.load(a.weights, map_location="cpu"))
            print(json.dumps(frcnn.evaluate(m, sp["test"], cats), indent=1))
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("meta", nargs="*"); ap.add_argument("--detector", choices=DETECTORS, default="none")
    ap.add_argument("--template"); ap.add_argument("--template-label", default="template")
    ap.add_argument("--threshold", type=float); ap.add_argument("--weights"); ap.add_argument("--classes")
    ap.add_argument("--out-dir", default="out/detections")
    a = ap.parse_args(argv)
    if a.detector == "none":
        print("detector: none (default) - nothing run"); return 0
    metas = [json.load(open(f)) for pat in a.meta for f in (glob.glob(pat) or [pat])]
    w = run(a.detector, metas, a.out_dir, a.template, a.template_label, a.threshold, a.weights, a.classes)
    print(f"{len(w)} candidate(s) for human review in {a.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
