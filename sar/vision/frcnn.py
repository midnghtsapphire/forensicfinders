"""torchvision Faster R-CNN fine-tuning, evaluation and inference (2110, --detector frcnn).

License: torchvision is BSD-3-Clause, so it can live in this private repo. The COCO-pretrained weights
are downloaded by torchvision on first use (check their terms before redistribution). Ultralytics
(AGPL) is deliberately not used.
"""
import numpy as np


def _torch():
    import torch, torchvision  # noqa: F401
    return torch


def build_model(num_classes, pretrained=True, small=True, **kw):
    """num_classes excludes background. small=True uses the MobileNetV3 FPN variant (CPU friendly).
    Extra kw (e.g. min_size, max_size) go to the torchvision constructor."""
    torch = _torch()
    from torchvision.models import detection as D
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    if small:
        m = D.fasterrcnn_mobilenet_v3_large_fpn(weights="DEFAULT" if pretrained else None,
                                                weights_backbone="DEFAULT" if pretrained else None, **kw)
    else:
        m = D.fasterrcnn_resnet50_fpn(weights="DEFAULT" if pretrained else None,
                                      weights_backbone="DEFAULT" if pretrained else None, **kw)
    inf = m.roi_heads.box_predictor.cls_score.in_features
    m.roi_heads.box_predictor = FastRCNNPredictor(inf, num_classes + 1)
    return m


def _load_image(path):
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"))


def to_target(im, cat_index):
    torch = _torch()
    b = [[x, y, x + w, y + h] for x, y, w, h in im["boxes"]]
    return {"boxes": torch.tensor(b, dtype=torch.float32).reshape(-1, 4),
            "labels": torch.tensor([cat_index[c] for c in im["labels"]], dtype=torch.int64)}


def _tensor(arr):
    torch = _torch()
    return torch.from_numpy(arr).permute(2, 0, 1).float() / 255.0


def train(model, images, cats, epochs=1, max_steps=None, lr=0.005, batch_size=2, device="cpu", log=print):
    """Fine-tune. cats: {coco_id: name}. Contiguous label ids 1..K follow sorted COCO ids."""
    torch = _torch()
    cat_index = {cid: i + 1 for i, cid in enumerate(sorted(cats))}
    model.to(device).train()
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.SGD(params, lr=lr, momentum=0.9, weight_decay=5e-4)
    step = 0
    for ep in range(epochs):
        order = np.random.default_rng(ep).permutation(len(images))
        for i in range(0, len(order), batch_size):
            batch = [images[j] for j in order[i:i + batch_size]]
            x = [_tensor(_load_image(im["file"])).to(device) for im in batch]
            y = [{k: v.to(device) for k, v in to_target(im, cat_index).items()} for im in batch]
            loss = sum(model(x, y).values())
            opt.zero_grad(); loss.backward(); opt.step()
            step += 1
            log(f"epoch {ep} step {step} loss {loss.item():.4f}")
            if max_steps and step >= max_steps:
                return {"steps": step, "last_loss": float(loss.item())}
    return {"steps": step, "last_loss": float(loss.item()) if step else None}


def predict(model, arr, score_threshold=0.5, device="cpu"):
    torch = _torch()
    model.to(device).eval()
    with torch.no_grad():
        out = model([_tensor(arr).to(device)])[0]
    res = []
    for b, s, l in zip(out["boxes"].tolist(), out["scores"].tolist(), out["labels"].tolist()):
        if s >= score_threshold:
            res.append({"box": [b[0], b[1], b[2] - b[0], b[3] - b[1]], "score": round(s, 4), "label_index": int(l)})
    return res


def evaluate(model, images, cats, device="cpu", iou_thr=0.5, score_threshold=0.05):
    """mAP@[.5:.95] and mAP@.5 via torchmetrics if installed, plus per-class recall at iou_thr (own code)."""
    cat_index = {cid: i + 1 for i, cid in enumerate(sorted(cats))}
    inv = {v: cats[k] for k, v in cat_index.items()}
    preds, gts = [], []
    for im in images:
        p = predict(model, _load_image(im["file"]), score_threshold, device)
        preds.append(p); gts.append(im)
    out = {"per_class_recall": per_class_recall(preds, gts, cat_index, inv, iou_thr)}
    try:
        torch = _torch()
        from torchmetrics.detection import MeanAveragePrecision
        mp = MeanAveragePrecision(box_format="xywh")
        mp.update([{"boxes": torch.tensor([q["box"] for q in p], dtype=torch.float32).reshape(-1, 4),
                    "scores": torch.tensor([q["score"] for q in p]),
                    "labels": torch.tensor([q["label_index"] for q in p], dtype=torch.int64)} for p in preds],
                  [{"boxes": torch.tensor(g["boxes"], dtype=torch.float32).reshape(-1, 4),
                    "labels": torch.tensor([cat_index[c] for c in g["labels"]], dtype=torch.int64)} for g in gts])
        r = mp.compute()
        out["mAP"] = float(r["map"]); out["mAP50"] = float(r["map_50"])
    except ImportError:
        out["mAP"] = None; out["note"] = "pip install torchmetrics for mAP"
    return out


def iou_xywh(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0.0, min(ax2, bx2) - max(a[0], b[0])); ih = max(0.0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    u = a[2] * a[3] + b[2] * b[3] - inter
    return inter / u if u > 0 else 0.0


def per_class_recall(preds, gts, cat_index, inv, iou_thr=0.5):
    """Fraction of ground-truth boxes per class matched by a same-class prediction at IoU >= iou_thr."""
    found, total = {}, {}
    for p, g in zip(preds, gts):
        used = set()
        for box, cid in zip(g["boxes"], g["labels"]):
            li = cat_index[cid]; total[li] = total.get(li, 0) + 1
            for k, q in enumerate(p):
                if k not in used and q["label_index"] == li and iou_xywh(box, q["box"]) >= iou_thr:
                    used.add(k); found[li] = found.get(li, 0) + 1; break
    return {inv[li]: round(found.get(li, 0) / n, 4) for li, n in total.items()}
