# Evaluation (2026-10-16 11:00)

Free-text farmer descriptions (Tamil, English, Tanglish) of all 17 diseases, written independently of the knowledge graph's lay-term phrases, followed by a simulated noisy dialogue.

85 cases × 20 simulated dialogues.

| Metric | v1 prototype | v2 + random questions | v2 (this system) |
|---|---:|---:|---:|
| Input understood | 91.8% | 100.0% | 100.0% |
| Top-1, description only | 63.5% | 92.9% | 92.9% |
| Top-1 after dialogue | 63.5% | 95.2% | 96.5% |
| Top-3 after dialogue | 85.9% | 99.5% | 99.9% |
| Confidently wrong | 10.6% | 0.6% | 1.0% |
| Avg. questions | — | 3.51 | 2.05 |
| Top-1 after dialogue, Tamil | 67.6% | 95.3% | 96.3% |
| Top-1 after dialogue, English | 52.9% | 95.4% | 97.1% |
| Top-1 after dialogue, Tanglish | 76.5% | 94.4% | 95.6% |

## Per disease (top-1 after dialogue)

| Disease | v1 prototype | v2 + random questions | v2 (this system) |
|---|---:|---:|---:|
| Early Blight | 80.0% | 100.0% | 95.0% |
| Late Blight | 60.0% | 94.0% | 100.0% |
| Powdery Mildew | 40.0% | 99.0% | 100.0% |
| Whitefly Infestation | 80.0% | 96.0% | 100.0% |
| Tomato Leaf Curl Virus | 60.0% | 98.0% | 99.0% |
| Septoria Leaf Spot | 80.0% | 94.0% | 99.0% |
| Bacterial Spot | 80.0% | 74.0% | 75.0% |
| Fusarium Wilt | 80.0% | 99.0% | 100.0% |
| Bacterial Wilt | 80.0% | 99.0% | 100.0% |
| Blossom End Rot | 40.0% | 92.0% | 98.0% |
| Tomato Mosaic Virus | 80.0% | 99.0% | 99.0% |
| Two-Spotted Spider Mite | 40.0% | 97.0% | 98.0% |
| Fruit Borer | 60.0% | 98.0% | 100.0% |
| Root-Knot Nematode | 60.0% | 100.0% | 100.0% |
| Leaf Miner | 60.0% | 95.0% | 97.0% |
| Leaf Mold | 100.0% | 98.0% | 99.0% |
| Target Spot | 0.0% | 86.0% | 81.0% |

> The test descriptions were written by the system's authors, and the simulated farmer answers according to the knowledge graph's own probabilities - so these numbers measure the reasoning pipeline, not field accuracy. A field study with real farmer descriptions is the next validation step.
