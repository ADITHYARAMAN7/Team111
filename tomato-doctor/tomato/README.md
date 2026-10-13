# Leaf-photo dataset (not in git)

The photo classifier (`models/leaf_classifier.onnx`) was trained on the tomato
classes of the **PlantVillage** dataset (10 classes: 9 diseases + healthy;
1,000 training and 100 validation images per class, ~206 MB). The images are
not committed. The trained model is, so the app works without them.

To retrain, place the images here:

```
tomato/train/Tomato___Bacterial_spot/*.jpg        (1000 per class)
tomato/train/Tomato___Early_blight/ ...
tomato/val/Tomato___Bacterial_spot/*.jpg          (100 per class)
...
```

Class folders: `Tomato___Bacterial_spot`, `Tomato___Early_blight`, `Tomato___healthy`,
`Tomato___Late_blight`, `Tomato___Leaf_Mold`, `Tomato___Septoria_leaf_spot`,
`Tomato___Spider_mites Two-spotted_spider_mite`, `Tomato___Target_Spot`,
`Tomato___Tomato_mosaic_virus`, `Tomato___Tomato_Yellow_Leaf_Curl_Virus`.

Source: PlantVillage (Hughes & Salathé, 2015, arXiv:1511.08060), tomato classes.
Then run `python scripts/train_vision.py`.
