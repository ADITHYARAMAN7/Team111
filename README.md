# MULTIMODAL CROP DISEASE IDENTIFICATION USING LLM AND KNOWLEDGE GRAPH

![Status: Phase 1 (Research & Proof of Concept)](https://img.shields.io/badge/Status-Phase_1_(PoC)-blue)
![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![HuggingFace](https://img.shields.io/badge/AI-HuggingFace-orange)
![Neo4j](https://img.shields.io/badge/Graph-Neo4j-008CC1)

> **TL;DR:** Challenging the 2025 Vision-Language Model (VLM) paradigm by proposing a "Voice-First, Vision-Retrieval" framework. This project combines Audio-Native LLMs with strict Knowledge Graphs to provide hallucination-free crop disease diagnosis for rural farmers, completely bypassing the need for high-end smartphone cameras.

---

## 🛑 The Problem: The Diagnostic "Trilemma"
Current state-of-the-art agricultural AI (like Multimodal Large Language Models) fails to bridge the "last-mile" gap for semi-literate farmers in low-resource environments due to three critical flaws:

1. **The Linguistic Barrier:** Farmers rely on spoken, code-mixed regional dialects (e.g., "Tanglish"). Cascaded ASR pipelines misinterpret these nuances.
2. **The Hardware Constraint (The "Camera Assumption"):** Modern AI requires high-resolution images. Low-end rural smartphone cameras in poor lighting cause visual misclassification.
3. **The Reliability Risk:** Pure Generative AI models hallucinate chemical treatments, posing severe economic and safety risks to crop yields.

## 💡 The Solution: The "Blind Doctor" Heuristic
Instead of forcing the edge device to "see" through a poor camera, we shift the diagnostic burden to intelligent, voice-driven dialogue and server-side symbolic logic. 

**Our Neuro-Symbolic Approach:**
* **Listen (Neuro):** Process raw regional audio to extract scientific crop and symptom entities.
* **Reason (Symbolic):** Traverse a deterministic Knowledge Graph to find the scientifically verified disease and cure.
* **Verify (RAG):** Retrieve a pristine, textbook-quality reference image of the disease from a database and ask the farmer for visual confirmation.



---

## ⚙️ System Architecture 

The pipeline consists of three core operational layers:

1. **Perception & Cognition (Audio-Native LLM):** Bypasses traditional Speech-to-Text. A model (e.g., Whisper/Qwen-Audio) processes raw acoustic features directly from regional dialects to extract `[Crop]` and `[Symptom]` entities.
2. **Deterministic Reasoning (Knowledge Graph):** Extracted entities are passed to a Neo4j Graph structured on the `VEG-MMKG` ontology. The graph strictly maps `(Crop) -> [HAS_SYMPTOM] -> (Disease) -> [TREATED_BY] -> (Chemical)`.
3. **Visual Verification (Retrieval-Augmented Generation):** Text embeddings of the verified disease are matched against a high-fidelity image database (e.g., PlantVillage/CDDM) using Cosine Similarity (`SentenceTransformers`). 



---

## 🚀 Phase 1: Current Implementation (Proof of Concept)
This repository currently contains the Phase 1 Jupyter/Colab notebooks demonstrating the foundational data processing and algorithmic routing:

* ✅ **End-to-End Audio Extraction PoC:** Processing real voice audio using OpenAI's `whisper` to accurately extract agricultural entities from code-mixed speech (Tanglish).
* ✅ **Knowledge Graph Triplet Generation:** Scripts to transform real-world datasets (Makerere University Beans Dataset) into relational graph triplets (`Subject`, `Predicate`, `Object`).
* ✅ **Vector Embedding for RAG:** Utilizing `all-MiniLM-L6-v2` to mathematically embed visual descriptions for the final image retrieval loop.

---

## 💻 Tech Stack
* **Audio Processing:** `librosa`, `soundfile`
* **AI / NLP Models:** `whisper` (OpenAI), `sentence-transformers` (HuggingFace)
* **Data Engineering:** `pandas`, `datasets` (HuggingFace)
* **Knowledge Graph:** `Neo4j` *(Upcoming Phase 2)*

---

## 🛠️ Getting Started (Running the Phase 1 PoC)

### Prerequisites
* Python 3.8+
* Google Colab (Recommended for immediate testing)

### Installation
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/yourusername/agronomist-neuro-symbolic.git](https://github.com/yourusername/agronomist-neuro-symbolic.git)
cd agronomist-neuro-symbolic
pip install -r requirements.txt
