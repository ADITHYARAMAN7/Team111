"""
train_vision.py - trains the leaf-photo classifier used as *one source of
evidence* in the diagnosis (the knowledge graph still makes the decision).

Approach (works on a CPU-only laptop in a few minutes):
  1. ImageNet-pretrained MobileNetV3-Large as a frozen feature extractor.
  2. Extract 960-d pooled features for every train image (+ its mirror image)
     and every val image, cached to models/features_cache.npz.
  3. Train a small MLP head on the features.
  4. Fit a softmax temperature on the val set (calibrated probabilities matter
     because the app fuses them with KG evidence).
  5. Export backbone + head as one ONNX graph -> models/leaf_classifier.onnx,
     so the web app only needs onnxruntime, not torch.

Dataset layout (PlantVillage subset already in this repo):
  tomato/train/<class folder>/*.jpg   (1000 per class)
  tomato/val/<class folder>/*.jpg     (100 per class)

Usage:  python scripts/train_vision.py
"""
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tomato")
OUT = os.path.join(ROOT, "models")
CACHE = os.path.join(OUT, "features_cache.npz")

# PlantVillage folder -> disease_id used in the knowledge graph
FOLDER_TO_ID = {
    "Tomato___Bacterial_spot": "bacterial_spot",
    "Tomato___Early_blight": "early_blight",
    "Tomato___Late_blight": "late_blight",
    "Tomato___Leaf_Mold": "leaf_mold",
    "Tomato___Septoria_leaf_spot": "septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite": "spider_mite",
    "Tomato___Target_Spot": "target_spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "leaf_curl_virus",
    "Tomato___Tomato_mosaic_virus": "mosaic_virus",
    "Tomato___healthy": "healthy",
}
LABELS = sorted(FOLDER_TO_ID.values())
IMG_SIZE = 224
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


class Backbone(nn.Module):
    def __init__(self):
        super().__init__()
        m = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        self.features, self.pool = m.features, m.avgpool

    def forward(self, x):
        return torch.flatten(self.pool(self.features(x)), 1)


class Head(nn.Module):
    def __init__(self, n_in=960, n_out=len(LABELS)):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(n_in, 256), nn.ReLU(), nn.Dropout(0.3), nn.Linear(256, n_out))

    def forward(self, f):
        return self.net(f)


class FullModel(nn.Module):
    """What gets exported: raw normalized image -> calibrated logits."""
    def __init__(self, backbone, head, temperature):
        super().__init__()
        self.backbone, self.head = backbone, head
        self.register_buffer("t", torch.tensor(float(temperature)))

    def forward(self, x):
        return self.head(self.backbone(x)) / self.t


def list_split(split):
    items = []
    for folder, did in FOLDER_TO_ID.items():
        d = os.path.join(DATA, split, folder)
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                items.append((os.path.join(d, f), LABELS.index(did)))
    return items


@torch.no_grad()
def extract(backbone, items, flip=False, bs=64):
    tf = transforms.Compose([transforms.Resize((IMG_SIZE, IMG_SIZE)), transforms.ToTensor(),
                             transforms.Normalize(MEAN, STD)])
    feats, t0 = [], time.time()
    for i in range(0, len(items), bs):
        batch = []
        for path, _ in items[i:i + bs]:
            img = Image.open(path).convert("RGB")
            if flip:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            batch.append(tf(img))
        feats.append(backbone(torch.stack(batch)).numpy())
        done = min(i + bs, len(items))
        if (i // bs) % 20 == 0:
            print(f"    {done}/{len(items)}  ({time.time() - t0:.0f}s)", flush=True)
    return np.concatenate(feats)


def main():
    torch.manual_seed(1337)
    np.random.seed(1337)
    torch.set_num_threads(os.cpu_count() or 4)
    os.makedirs(OUT, exist_ok=True)

    backbone = Backbone().eval()
    train_items, val_items = list_split("train"), list_split("val")
    print(f"train={len(train_items)} val={len(val_items)} classes={len(LABELS)}")

    if os.path.exists(CACHE):
        c = np.load(CACHE)
        Xtr, ytr, Xva, yva = c["Xtr"], c["ytr"], c["Xva"], c["yva"]
        print("loaded cached features")
    else:
        print("extracting train features..."); a = extract(backbone, train_items)
        print("extracting mirrored train features..."); b = extract(backbone, train_items, flip=True)
        print("extracting val features..."); Xva = extract(backbone, val_items)
        Xtr = np.concatenate([a, b])
        ytr = np.array([y for _, y in train_items] * 2)
        yva = np.array([y for _, y in val_items])
        np.savez_compressed(CACHE, Xtr=Xtr, ytr=ytr, Xva=Xva, yva=yva)

    Xtr_t, ytr_t = torch.tensor(Xtr), torch.tensor(ytr)
    Xva_t, yva_t = torch.tensor(Xva), torch.tensor(yva)

    head = Head()
    opt = torch.optim.AdamW(head.parameters(), lr=2e-3, weight_decay=1e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=40)
    lossf = nn.CrossEntropyLoss(label_smoothing=0.05)
    best, best_state = 0.0, None
    for epoch in range(40):
        head.train()
        perm = torch.randperm(len(Xtr_t))
        for i in range(0, len(perm), 256):
            idx = perm[i:i + 256]
            # feature-space noise as a cheap extra augmentation
            x = Xtr_t[idx] + 0.05 * torch.randn_like(Xtr_t[idx])
            opt.zero_grad()
            lossf(head(x), ytr_t[idx]).backward()
            opt.step()
        sched.step()
        head.eval()
        with torch.no_grad():
            acc = (head(Xva_t).argmax(1) == yva_t).float().mean().item()
        if acc >= best:
            best, best_state = acc, {k: v.clone() for k, v in head.state_dict().items()}
        if epoch % 5 == 4:
            print(f"  epoch {epoch + 1:2d}  val_acc={acc:.4f}")
    head.load_state_dict(best_state)
    head.eval()

    # temperature scaling on val logits
    with torch.no_grad():
        logits = head(Xva_t)
    log_t = torch.zeros(1, requires_grad=True)
    topt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=200)

    def closure():
        topt.zero_grad()
        l = nn.functional.cross_entropy(logits / log_t.exp(), yva_t)
        l.backward()
        return l
    topt.step(closure)
    temperature = float(log_t.exp().item())

    preds = logits.argmax(1).numpy()
    n = len(LABELS)
    cm = np.zeros((n, n), dtype=int)
    for t, p in zip(yva, preds):
        cm[t, p] += 1
    per_class = {}
    for i, lab in enumerate(LABELS):
        tp = cm[i, i]
        prec = tp / max(1, cm[:, i].sum())
        rec = tp / max(1, cm[i, :].sum())
        per_class[lab] = {"precision": round(float(prec), 4), "recall": round(float(rec), 4),
                          "f1": round(float(2 * prec * rec / max(1e-9, prec + rec)), 4)}

    full = FullModel(backbone, head, temperature).eval()
    onnx_path = os.path.join(OUT, "leaf_classifier.onnx")
    dummy = torch.randn(1, 3, IMG_SIZE, IMG_SIZE)
    torch.onnx.export(full, dummy, onnx_path, input_names=["image"], output_names=["logits"],
                      dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}}, opset_version=17)

    # sanity: onnxruntime must agree with torch
    import onnxruntime as ort
    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    with torch.no_grad():
        ref = full(dummy).numpy()
    got = sess.run(None, {"image": dummy.numpy()})[0]
    assert np.allclose(ref, got, atol=1e-3), "ONNX export mismatch"

    meta = {
        "labels": LABELS, "img_size": IMG_SIZE, "mean": MEAN, "std": STD,
        "temperature": round(temperature, 4), "backbone": "mobilenet_v3_large (ImageNet, frozen)",
        "train_images": len(train_items) * 2, "val_images": len(val_items),
        "val_accuracy": round(float((preds == yva).mean()), 4),
        "per_class": per_class, "confusion_matrix": cm.tolist(),
        "note": "Validation images come from the same PlantVillage distribution (lab photos, "
                "plain background). Expect lower accuracy on field photos - which is why the app "
                "fuses this as soft evidence with the knowledge graph rather than trusting it alone.",
        "trained_at": time.strftime("%Y-%m-%d %H:%M"),
    }
    with open(os.path.join(OUT, "leaf_classifier.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"\nval accuracy {meta['val_accuracy']:.4f}, temperature {temperature:.3f}")
    print(f"saved {onnx_path}")


if __name__ == "__main__":
    sys.exit(main())
