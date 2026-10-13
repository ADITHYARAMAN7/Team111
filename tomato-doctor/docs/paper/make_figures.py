"""Builds every chart in the paper from results/*.json (run scripts/experiments.py first).
    python docs/paper/make_figures.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

COL = 3.5      # IEEE single column (in)
DBL = 7.16     # IEEE double column
FOREST, TOMATO, GOLD, SLATE, LEAF, GREY = "#2f5d34", "#c8432b", "#b88a12", "#3b5b7a", "#7fa35a", "#8a8a8a"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "mathtext.fontset": "stix",
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def load(name):
    with open(os.path.join(RES, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def save(fig, name):
    fig.savefig(os.path.join(FIG, f"{name}.pdf"))
    fig.savefig(os.path.join(FIG, f"{name}.png"), dpi=200)
    plt.close(fig)
    print("figure", name)


NAMES = {}


def names():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
    from tomatodoc.kg.graph import load_seed
    for d in load_seed()["diseases"]:
        NAMES[d["id"]] = d["name_en"].replace("Tomato ", "").replace("Two-Spotted ", "").replace(" Infestation", "")
    NAMES["unknown"] = "Unknown"
    NAMES["healthy"] = "Healthy"


# ---------------------------------------------------------------- dialogue trace
def fig_dialogue():
    tr = load("e2_budget")["white_dust_trace"]
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.75), sharey=True)
    for ax, t, tag in zip(axes, tr["traces"], ("(a)", "(b)")):
        steps = t["steps"]
        xs = np.arange(len(steps))
        for did, col, mk in (("powdery_mildew", GOLD, "o"), ("whitefly", SLATE, "s")):
            ys = [next((p["p"] for p in s["posterior"] if p["id"] == did), 0) for s in steps]
            ax.plot(xs, ys, marker=mk, ms=3.2, lw=1.2, color=col, label=NAMES[did])
        ax.axhline(0.85, ls="--", lw=0.6, color=GREY)
        ax.set_xticks(xs, ["text"] + [f"Q{i}" for i in range(1, len(steps))])
        for i, s in enumerate(steps[:-1]):
            ax.text(i + 1, 1.04, s["answer"], ha="center", fontsize=6, color=TOMATO if s["answer"] == "yes" else GREY)
        ax.text(-0.15, 0.875, "stop", fontsize=5.5, color=GREY)
        ax.set_xlabel(f"{tag} truth: {NAMES[t['truth']]}", labelpad=2)
        ax.set_ylim(0, 1.1)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.grid(axis="y", lw=0.3, alpha=0.5)
    axes[0].set_ylabel("posterior $P(d\mid E)$")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.55, 1.07))
    fig.tight_layout(w_pad=0.6)
    save(fig, "dialogue_trace")


# ---------------------------------------------------------------- budget curves
def fig_budget():
    r = load("e2_budget")
    fig, ax = plt.subplots(figsize=(COL, 1.7))
    style = {"eig": (TOMATO, "o", "Expected information gain (proposed)"), "variance": (SLATE, "s", "Weight variance (v1 rule)"),
             "random": (GREY, "^", "Random symptom")}
    for k, (c, m, lab) in style.items():
        ax.plot(r["budgets"], [100 * v for v in r["curves"][k]], marker=m, ms=3.5, lw=1.2, color=c, label=lab)
    ax.set_xlabel("maximum number of follow-up questions")
    ax.set_ylabel("top-1 accuracy (%)")
    ax.set_xticks(r["budgets"])
    ax.grid(lw=0.3, alpha=0.5)
    ax.set_ylim(90.5, 97.8)
    ax.legend(frameon=False, loc="lower right", fontsize=6.5)
    save(fig, "budget_curves")


# ---------------------------------------------------------------- per disease
def fig_per_disease():
    r = load("e1_accuracy")["per_disease"]
    r = sorted(r, key=lambda x: (x["eig"], x["v1"]))
    fig, ax = plt.subplots(figsize=(COL, 2.75))
    y = np.arange(len(r))
    ax.barh(y + 0.2, [100 * x["v1"] for x in r], height=0.38, color="#c9c2ad", label="v1 prototype")
    ax.barh(y - 0.2, [100 * x["eig"] for x in r], height=0.38, color=FOREST, label="Proposed")
    ax.set_yticks(y, [NAMES[x["disease"]] for x in r])
    ax.set_xlabel("top-1 accuracy after dialogue (%)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2)
    save(fig, "per_disease")


# ---------------------------------------------------------------- learning
def fig_learning():
    r = load("e4_learning")
    w = r["window"]
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.6))
    style = {"beta": (FOREST, "Beta, confirmed-only (proposed)"), "v1": (TOMATO, "v1 $\\pm$0.03 rule"), "none": (GREY, "no learning")}
    for k, (c, lab) in style.items():
        m = np.array(r["rules"][k]["accuracy_mean"]) * 100
        sd = np.array(r["rules"][k]["accuracy_sd"]) * 100
        x = np.arange(1, len(m) + 1) * w
        axes[0].plot(x, m, color=c, lw=1.1, label=lab)
        axes[0].fill_between(x, m - sd, m + sd, color=c, alpha=0.15, lw=0)
        mae = r["rules"][k]["mae_mean"]
        axes[1].plot(np.arange(len(mae)) * w, mae, color=c, lw=1.1)
    axes[0].set_xlabel("consultations")
    axes[0].set_ylabel("accuracy (%), window 100")
    axes[1].set_xlabel("consultations")
    axes[1].set_ylabel("mean |$\\theta-\\theta^{*}$|")
    for ax, tag in zip(axes, ("(a)", "(b)")):
        ax.grid(lw=0.3, alpha=0.5)
        ax.set_title(tag, pad=2)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.1), fontsize=6.3)
    fig.tight_layout(w_pad=1.0)
    save(fig, "learning")


# ---------------------------------------------------------------- vision
def fig_vision():
    r = load("e3_vision")
    meta = r["classifier_meta"]
    labels = meta["labels"]
    cm = np.array(meta["confusion_matrix"], dtype=float)
    cmn = cm / cm.sum(axis=1, keepdims=True)
    short = {"bacterial_spot": "Bact. spot", "early_blight": "Early bl.", "healthy": "Healthy", "late_blight": "Late bl.",
             "leaf_curl_virus": "Leaf curl", "leaf_mold": "Leaf mold", "mosaic_virus": "Mosaic", "septoria_leaf_spot": "Septoria",
             "spider_mite": "Spider mite", "target_spot": "Target sp."}
    fig = plt.figure(figsize=(DBL, 2.25))
    ax = fig.add_axes([0.06, 0.2, 0.36, 0.75])
    im = ax.imshow(cmn, cmap="Greens", vmin=0, vmax=1)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j]:
                ax.text(j, i, int(cm[i, j]), ha="center", va="center", fontsize=5.5, color="white" if cmn[i, j] > 0.5 else "black")
    ax.set_xticks(range(len(labels)), [short[l] for l in labels], rotation=60, ha="right")
    ax.set_yticks(range(len(labels)), [short[l] for l in labels])
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title("(a) confusion matrix, clean validation set (n = 1000)", pad=3)
    for s in ax.spines.values():
        s.set_visible(False)
    ax2 = fig.add_axes([0.56, 0.2, 0.42, 0.68])
    groups = ["clean", "degraded"]
    bars = [("classifier_top1", "#c9c2ad", "classifier alone"), ("photo_only_engine_top1", SLATE, "photo $\\rightarrow$ KG posterior"),
            ("photo_plus_dialogue_top1", FOREST, "photo + KG dialogue")]
    x = np.arange(len(groups))
    for k, (key, col, lab) in enumerate(bars):
        vals = [100 * r[g][key] for g in groups]
        b = ax2.bar(x + (k - 1) * 0.26, vals, width=0.25, color=col, label=lab)
        for rect, v in zip(b, vals):
            ax2.text(rect.get_x() + rect.get_width() / 2, v + 1.2, f"{v:.1f}", ha="center", fontsize=6)
    ax2.set_xticks(x, ["clean (n = 900)", "field-like degraded (n = 900)"])
    ax2.set_ylabel("top-1 accuracy (%)")
    ax2.set_ylim(0, 108)
    ax2.legend(frameon=False, loc="upper right", fontsize=6.3)
    ax2.set_title("(b) robustness: classifier vs. fusion with dialogue", pad=3)
    ax2.grid(axis="y", lw=0.3, alpha=0.5)
    save(fig, "vision")


# ---------------------------------------------------------------- weather
def fig_weather():
    r = load("e6_weather")
    sites = r["sites"]
    dis = list(sites[0]["risks"])
    order = sorted(dis, key=lambda d: -max(s["risks"][d]["score"] for s in sites))
    m = np.array([[s["risks"][d]["score"] for d in order] for s in sites])
    fig, ax = plt.subplots(figsize=(COL, 1.75))
    ax.imshow(m, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            lvl = sites[i]["risks"][order[j]]["level"][0].upper()
            ax.text(j, i, lvl, ha="center", va="center", fontsize=6, color="white" if m[i, j] > 0.6 else "black")
    ax.set_xticks(range(len(order)), [NAMES[d] for d in order], rotation=55, ha="right")
    ax.set_yticks(range(len(sites)), [s["name"].replace("The Nilgiris (Ooty)", "Nilgiris (Ooty)") for s in sites])
    for s in ax.spines.values():
        s.set_visible(False)
    save(fig, "weather_risk")


if __name__ == "__main__":
    names()
    fig_dialogue()
    fig_budget()
    fig_per_disease()
    fig_learning()
    fig_vision()
    fig_weather()
