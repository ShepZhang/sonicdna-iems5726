"""KMeans mood clustering + PCA 2D embedding for SonicDNA.

We fit a single KMeans (k=8) on the standardized 9-dim audio feature
space. The cluster labels feed two downstream consumers:

    1. MoodPrint: cluster distribution drives the concentric ring colors
    2. MBTI: per-cluster centroids are sanity-checked against the 4-axis rule

A 2-D PCA projection is also fitted so the Insights tab can show the
user playlist on a global music map without re-running PCA every time.

Run:
    python -m pipeline.cluster
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from .config import (
    FEATURE_COLS,
    MODELS_DIR,
    MOOD_K,
    MOOD_KMEANS_PATH,
    PROCESSED_PARQUET_PATH,
    RANDOM_STATE,
)


def _scaled_columns() -> list[str]:
    return [f"{c}_z" for c in FEATURE_COLS]


def fit_mood_kmeans(df: pd.DataFrame) -> tuple[KMeans, np.ndarray]:
    """Fit KMeans on z-scored features, return model and assignments."""
    X = df[_scaled_columns()].to_numpy(dtype=np.float64)
    km = KMeans(
        n_clusters=MOOD_K,
        random_state=RANDOM_STATE,
        n_init=10,
        max_iter=300,
    )
    labels = km.fit_predict(X)
    print(f"[mood-kmeans] inertia={km.inertia_:.0f}")
    return km, labels


def fit_pca(df: pd.DataFrame) -> tuple[PCA, np.ndarray]:
    """Fit a 2-D PCA used for the Insights scatter."""
    X = df[_scaled_columns()].to_numpy(dtype=np.float64)
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(X)
    print(f"[pca] explained_variance_ratio={pca.explained_variance_ratio_}")
    return pca, coords


def name_mood_clusters(km: KMeans) -> dict[int, str]:
    """Heuristically name each cluster by inspecting its centroid in
    standardized space. Names are intentionally evocative (used in UI)
    and not meant to be psychometric labels.

    Rule order matters: the first matching rule wins. We start with
    the most uniquely identifiable signatures (rap, live, classical)
    before falling through to generic energy/valence quadrants.
    """
    centers = km.cluster_centers_
    names: dict[int, str] = {}
    used: set[str] = set()

    def _pick(f: dict[str, float]) -> str:
        # Highly distinctive single-feature signatures first.
        if f["speechiness"] > 1.0:
            return "Cipher Booth"
        if f["liveness"] > 1.5:
            return "Live Stage Glow"
        if f["instrumentalness"] > 1.0 and f["acousticness"] > 0.5:
            return "Library Hush"
        if f["instrumentalness"] > 1.0:
            return "Drift Layer"
        # Energy x valence quadrants.
        if f["energy"] > 0.4 and f["valence"] < -0.2:
            return "Stormcore Drive"
        if f["energy"] < -0.5 and f["acousticness"] > 0.5:
            return "Rainy Window"
        if f["valence"] > 0.5 and f["danceability"] > 0.5:
            return "Sunlit Indie"
        if f["popularity"] > 0.8:
            return "Mainstream Pulse"
        if f["energy"] > 0.5 and f["danceability"] > 0:
            return "Neon Pulse"
        return "Drift Layer"

    for i, c in enumerate(centers):
        f = dict(zip(FEATURE_COLS, c))
        label = _pick(f)
        if label in used:
            label = f"{label} {i}"
        used.add(label)
        names[i] = label
    return names


def main() -> None:
    print(f"[load] {PROCESSED_PARQUET_PATH}")
    df = pd.read_parquet(PROCESSED_PARQUET_PATH)
    print(f"[load] shape={df.shape}")

    km, labels = fit_mood_kmeans(df)
    df["mood_cluster"] = labels.astype(np.int16)

    pca, coords = fit_pca(df)
    df["pca_x"] = coords[:, 0]
    df["pca_y"] = coords[:, 1]

    names = name_mood_clusters(km)
    df["mood_label"] = df["mood_cluster"].map(names)
    print("[label] cluster names:")
    for k, v in names.items():
        n = (df["mood_cluster"] == k).sum()
        print(f"        {k}: {v:<20s} ({n:,} tracks)")

    # Persist back to parquet so the streamlit app reads from one source.
    df.to_parquet(PROCESSED_PARQUET_PATH, compression="snappy")

    # Persist sklearn artifacts.
    joblib.dump(km, MOOD_KMEANS_PATH)
    joblib.dump(pca, MODELS_DIR / "pca.pkl")

    # Save cluster names dict as a small JSON for the UI.
    import json
    (MODELS_DIR / "mood_cluster_names.json").write_text(
        json.dumps(names, indent=2, ensure_ascii=False)
    )

    print(f"[done] saved {MOOD_KMEANS_PATH.name}, pca.pkl, mood_cluster_names.json")
    print(f"[done] parquet now has {df.shape[1]} columns")


if __name__ == "__main__":
    main()
