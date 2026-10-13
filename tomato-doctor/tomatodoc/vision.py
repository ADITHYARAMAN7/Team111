"""
vision.py - leaf-photo classifier (ONNX, CPU) + photo quality checks.

The classifier is trained by scripts/train_vision.py on PlantVillage tomato
leaves. Its output is never shown as "the diagnosis": it is fused with the
knowledge-graph evidence in inference.py as a tempered likelihood.
"""
import io
import json
import logging
import os

import numpy as np
from PIL import Image, ImageOps

log = logging.getLogger(__name__)


class LeafClassifier:
    def __init__(self, model_path, meta_path):
        import onnxruntime as ort
        with open(meta_path, encoding="utf-8") as f:
            self.meta = json.load(f)
        self.labels = self.meta["labels"]
        self.size = self.meta["img_size"]
        self.mean = np.array(self.meta["mean"], dtype=np.float32).reshape(3, 1, 1)
        self.std = np.array(self.meta["std"], dtype=np.float32).reshape(3, 1, 1)
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])

    @staticmethod
    def load_image(data):
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img).convert("RGB")
        return img

    @staticmethod
    def quality(img):
        """Cheap checks that catch the most common bad field photos."""
        small = np.asarray(img.resize((256, 256)), dtype=np.float32)
        gray = small.mean(axis=2)
        brightness = float(gray.mean())
        lap = (gray[1:-1, 1:-1] * 4 - gray[:-2, 1:-1] - gray[2:, 1:-1] - gray[1:-1, :-2] - gray[1:-1, 2:])
        sharpness = float(lap.var())
        r, g, b = small[..., 0], small[..., 1], small[..., 2]
        plant = ((g > r * 0.9) & (g > b * 1.05)) | ((r > 90) & (g > 70) & (b < g * 0.8))   # green or yellow/brown foliage
        plant_fraction = float(plant.mean())
        issues = []
        if brightness < 45:
            issues.append("too_dark")
        if brightness > 235:
            issues.append("too_bright")
        if sharpness < 25:
            issues.append("blurry")
        if plant_fraction < 0.12:
            issues.append("no_leaf")
        return {"brightness": round(brightness, 1), "sharpness": round(sharpness, 1),
                "plant_fraction": round(plant_fraction, 3), "issues": issues}

    def _tensor(self, img):
        w, h = img.size
        side = min(w, h)                              # centre square crop
        img = img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
        img = img.resize((self.size, self.size), Image.BILINEAR)
        x = np.asarray(img, dtype=np.float32).transpose(2, 0, 1) / 255.0
        return ((x - self.mean) / self.std)[None].astype(np.float32)

    def predict(self, data):
        img = self.load_image(data)
        q = self.quality(img)
        logits = self.session.run(None, {"image": self._tensor(img)})[0][0]
        e = np.exp(logits - logits.max())
        p = e / e.sum()
        probs = {lab: float(v) for lab, v in zip(self.labels, p)}
        top = max(probs, key=probs.get)
        # how much to trust this photo when fusing with the graph
        temperature = 0.6
        if q["issues"] or probs[top] < 0.5:
            temperature = 0.25
        if "no_leaf" in q["issues"]:
            temperature = 0.0
        return {"probs": {k: round(v, 4) for k, v in probs.items()}, "top": top, "top_p": round(probs[top], 4),
                "quality": q, "temperature": temperature}


def load_classifier(model_dir):
    model = os.path.join(model_dir, "leaf_classifier.onnx")
    meta = os.path.join(model_dir, "leaf_classifier.json")
    if not (os.path.exists(model) and os.path.exists(meta)):
        log.info("Leaf classifier not found in %s - photo diagnosis disabled", model_dir)
        return None
    try:
        return LeafClassifier(model, meta)
    except Exception as e:  # noqa: BLE001
        log.warning("Could not load leaf classifier: %s", e)
        return None
