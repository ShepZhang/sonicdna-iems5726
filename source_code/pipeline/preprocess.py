"""Data preprocessing for SonicDNA.

Pipeline:
    raw CSV  ->  dedupe  ->  drop NaN core fields  ->  genre meta-grouping
              ->  StandardScaler on 9 audio features  ->  parquet + scaler.pkl

Run:
    python -m pipeline.preprocess
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .config import (
    DATA_PROCESSED_DIR,
    FEATURE_COLS,
    MODELS_DIR,
    PROCESSED_PARQUET_PATH,
    RAW_CSV_PATH,
    SCALER_PATH,
)

# 114 fine-grained Spotify genres get bucketed into 12 broad meta-genres.
# This collapses noise for the recommender's diversity constraints and
# produces interpretable axes for the Insights tab.
GENRE_META_MAP: dict[str, str] = {
    # pop family
    "pop": "Pop", "indie-pop": "Pop", "pop-film": "Pop",
    "j-pop": "Pop", "k-pop": "Pop", "mandopop": "Pop",
    "cantopop": "Pop", "malay": "Pop", "swedish": "Pop",
    "power-pop": "Pop", "synth-pop": "Pop",
    # rock family
    "rock": "Rock", "alt-rock": "Rock", "alternative": "Rock",
    "hard-rock": "Rock", "punk-rock": "Rock", "indie": "Rock",
    "j-rock": "Rock", "rock-n-roll": "Rock", "rockabilly": "Rock",
    "psych-rock": "Rock", "grunge": "Rock", "emo": "Rock",
    "goth": "Rock", "punk": "Rock", "garage": "Rock",
    # metal/heavy
    "metal": "Metal", "heavy-metal": "Metal", "black-metal": "Metal",
    "death-metal": "Metal", "metalcore": "Metal", "grindcore": "Metal",
    "hardcore": "Metal", "industrial": "Metal",
    # hip-hop / r&b / soul
    "hip-hop": "HipHop", "r-n-b": "HipHop", "soul": "HipHop",
    "trip-hop": "HipHop", "funk": "HipHop", "gospel": "HipHop", "groove": "HipHop",
    # electronic
    "edm": "Electronic", "electronic": "Electronic", "electro": "Electronic",
    "house": "Electronic", "deep-house": "Electronic", "chicago-house": "Electronic",
    "progressive-house": "Electronic", "techno": "Electronic",
    "minimal-techno": "Electronic", "detroit-techno": "Electronic",
    "trance": "Electronic", "drum-and-bass": "Electronic", "dubstep": "Electronic",
    "breakbeat": "Electronic", "dub": "Electronic", "hardstyle": "Electronic",
    "idm": "Electronic", "dance": "Electronic", "party": "Electronic",
    "club": "Electronic", "j-dance": "Electronic", "new-age": "Electronic",
    "disco": "Electronic",
    # jazz / blues / classical
    "jazz": "Jazz", "blues": "Jazz", "bluegrass": "Jazz",
    "classical": "Jazz", "opera": "Jazz", "show-tunes": "Jazz", "piano": "Jazz",
    # folk / acoustic / country
    "folk": "Folk", "acoustic": "Folk", "singer-songwriter": "Folk",
    "songwriter": "Folk", "country": "Folk", "honky-tonk": "Folk", "guitar": "Folk",
    # latin / brazil / caribbean
    "latin": "Latin", "latino": "Latin", "salsa": "Latin",
    "samba": "Latin", "brazil": "Latin", "mpb": "Latin",
    "forro": "Latin", "pagode": "Latin", "sertanejo": "Latin",
    "reggaeton": "Latin", "dancehall": "Latin", "reggae": "Latin",
    "ska": "Latin", "tango": "Latin", "spanish": "Latin",
    # world / regional
    "afrobeat": "World", "indian": "World", "iranian": "World",
    "turkish": "World", "world-music": "World", "french": "World",
    "german": "World", "british": "World",
    # chill / ambient / mood
    "chill": "Chill", "ambient": "Chill", "study": "Chill",
    "sleep": "Chill", "romance": "Chill", "sad": "Chill", "happy": "Chill",
    # niche
    "anime": "Niche", "children": "Niche", "kids": "Niche",
    "comedy": "Niche", "disney": "Niche", "j-idol": "Niche",
}

CORE_FIELDS = ["track_id", "artists", "track_name"]


def _ensure_dirs(paths: Iterable[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def load_raw(path: Path = RAW_CSV_PATH) -> pd.DataFrame:
    """Load raw Spotify Tracks CSV into a typed DataFrame."""
    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {path}. "
            "Run kagglehub download first or place dataset.csv manually."
        )
    df = pd.read_csv(path)
    # Drop pandas index column produced by the original Kaggle export.
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate, drop NaN in core fields, attach meta-genre column."""
    n_in = len(df)

    df = df.dropna(subset=CORE_FIELDS).copy()
    df = df.drop_duplicates(subset=["track_id"], keep="first")

    # The dataset duplicates many tracks across genre slices (one row per
    # (track, genre) pair). De-duplicating on track_id collapses those
    # to a single row whose genre is the first-seen one. We separately
    # keep the meta-genre column for downstream diversity logic.
    df["meta_genre"] = (
        df["track_genre"].map(GENRE_META_MAP).fillna("Other")
    )

    n_out = len(df)
    print(f"[clean] {n_in:,} rows in -> {n_out:,} rows out "
          f"({n_in - n_out:,} dropped)")
    return df.reset_index(drop=True)


def fit_scaler(df: pd.DataFrame) -> tuple[StandardScaler, np.ndarray]:
    """Fit StandardScaler on the 9 audio features used everywhere downstream."""
    matrix = df[FEATURE_COLS].to_numpy(dtype=np.float64)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    return scaler, scaled


def build_processed(df: pd.DataFrame, scaled: np.ndarray) -> pd.DataFrame:
    """Concatenate raw + scaled feature columns side by side."""
    scaled_cols = [f"{c}_z" for c in FEATURE_COLS]
    scaled_df = pd.DataFrame(scaled, columns=scaled_cols, index=df.index)
    return pd.concat([df, scaled_df], axis=1)


def main() -> None:
    _ensure_dirs([DATA_PROCESSED_DIR, MODELS_DIR])

    print(f"[load] reading {RAW_CSV_PATH}")
    df = load_raw()
    print(f"[load] shape={df.shape}")

    df = clean(df)

    print("[scale] fitting StandardScaler on 9 audio features ...")
    scaler, scaled = fit_scaler(df)
    out = build_processed(df, scaled)

    print(f"[save] {PROCESSED_PARQUET_PATH}")
    out.to_parquet(PROCESSED_PARQUET_PATH, compression="snappy")

    print(f"[save] {SCALER_PATH}")
    joblib.dump(scaler, SCALER_PATH)

    # Persist meta-genre frequency table for the report.
    meta_counts = out["meta_genre"].value_counts().to_dict()
    (MODELS_DIR / "meta_genre_counts.json").write_text(
        json.dumps(meta_counts, indent=2, ensure_ascii=False)
    )

    print(f"[done] processed shape = {out.shape}")
    print("[done] meta-genre distribution:")
    for k, v in sorted(meta_counts.items(), key=lambda kv: -kv[1]):
        print(f"        {k:<12s} {v:>6d}")


if __name__ == "__main__":
    main()
