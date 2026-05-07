"""Render the report's two system-architecture diagrams.

Output: ``source_code/models/figures/06_arch_mvp.png`` and
        ``source_code/models/figures/07_arch_production.png``

Both diagrams use plain matplotlib boxes + arrows so we don't need a
graphviz install; readability is more important than polish here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.config import MODELS_DIR  # noqa: E402

OUT = MODELS_DIR / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def _box(ax, x, y, w, h, label, color, text_color="white", fontsize=10):
    box = mpatches.FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=color, edgecolor="white", linewidth=1.5, zorder=2,
    )
    ax.add_patch(box)
    ax.text(x, y, label, ha="center", va="center",
            color=text_color, fontsize=fontsize, fontweight="bold", zorder=3)


def _arrow(ax, x1, y1, x2, y2, color="#888"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
        zorder=1,
    )


def render_mvp() -> Path:
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="#15151f")
    ax.set_facecolor("#15151f")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    _box(ax, 1.2, 4.5, 1.8, 0.9, "User\nBrowser", "#3f3f5e")
    _box(ax, 4.0, 4.5, 2.0, 0.9, "Streamlit App\n(app.py)", "#FF4DB8")

    _box(ax, 7.2, 5.3, 1.8, 0.7, "MoodPrint", "#FFD256", "black", 9)
    _box(ax, 7.2, 4.5, 1.8, 0.7, "Music MBTI", "#5BA8FF", fontsize=9)
    _box(ax, 7.2, 3.7, 1.8, 0.7, "Parallel Universe", "#9F7BFF", fontsize=9)
    _box(ax, 7.2, 2.9, 1.8, 0.7, "Recommender", "#5DE26A", "black", 9)

    _box(ax, 10.4, 4.5, 2.0, 1.6,
         "Pretrained Models\nKMeans  +  PCA\n+ Scaler\n+ MBTI thresholds",
         "#1f1f2e", fontsize=9)

    _arrow(ax, 2.1, 4.5, 3.0, 4.5, "#fff")
    for y in [5.3, 4.5, 3.7, 2.9]:
        _arrow(ax, 5.0, 4.5, 6.3, y, "#aaa")
        _arrow(ax, 8.1, y, 9.4, 4.5, "#666")

    _box(ax, 4.0, 1.2, 9.0, 0.7,
         "Docker container · runs on HuggingFace Spaces / local docker run",
         "#2a2a40", fontsize=10)

    ax.text(0.3, 5.7, "Current MVP Architecture",
            color="white", fontsize=14, fontweight="bold")

    fig.savefig(OUT / "06_arch_mvp.png", dpi=140, bbox_inches="tight",
                facecolor="#15151f")
    plt.close(fig)
    return OUT / "06_arch_mvp.png"


def render_production() -> Path:
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="#15151f")
    ax.set_facecolor("#15151f")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    _box(ax, 1.2, 4.5, 1.8, 0.9, "User\nBrowser", "#3f3f5e")
    _box(ax, 3.6, 4.5, 1.6, 0.9, "NGINX\n(reverse proxy)", "#1f6e8c", fontsize=9)

    _box(ax, 6.2, 5.4, 1.8, 0.8, "Vue3 + Vite\n(SPA frontend)", "#42b883", fontsize=9)
    _box(ax, 6.2, 3.6, 1.8, 0.8, "FastAPI\n(backend)", "#009485", fontsize=9)

    _box(ax, 9.0, 5.4, 1.8, 0.8, "Pipeline package\n(unchanged)",
         "#FF4DB8", fontsize=9)
    _box(ax, 9.0, 3.6, 1.8, 0.8, "MySQL\n(history)", "#3f51b5", fontsize=9)
    _box(ax, 11.1, 3.6, 1.4, 0.8, "Redis\n(cache)", "#a52a2a", fontsize=9)

    _arrow(ax, 2.1, 4.5, 2.8, 4.5, "#fff")
    _arrow(ax, 4.4, 4.7, 5.3, 5.3, "#aaa")
    _arrow(ax, 4.4, 4.3, 5.3, 3.7, "#aaa")
    _arrow(ax, 7.1, 5.4, 8.1, 5.4, "#aaa")
    _arrow(ax, 7.1, 3.6, 8.1, 3.6, "#aaa")
    _arrow(ax, 9.9, 3.6, 10.5, 3.6, "#aaa")
    _arrow(ax, 7.1, 5.0, 8.1, 4.0, "#666")

    _box(ax, 6.0, 1.2, 10.0, 0.7,
         "Kubernetes deployment · CDN-cached SPA · monitored via Prometheus",
         "#2a2a40", fontsize=10)

    ax.text(0.3, 5.7, "Future Production Architecture",
            color="white", fontsize=14, fontweight="bold")

    fig.savefig(OUT / "07_arch_production.png", dpi=140, bbox_inches="tight",
                facecolor="#15151f")
    plt.close(fig)
    return OUT / "07_arch_production.png"


if __name__ == "__main__":
    print(f"[arch] saved {render_mvp()}")
    print(f"[arch] saved {render_production()}")
