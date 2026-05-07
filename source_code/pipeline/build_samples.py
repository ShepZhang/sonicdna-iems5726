"""Build three demo playlists for the Streamlit app.

Saves CSVs under ``application/samples/``. Each CSV contains the
9 audio feature columns the rest of the pipeline expects, plus
metadata (track_id / track_name / artists / track_genre).

Run:
    python -m pipeline.build_samples
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import FEATURE_COLS, PROCESSED_PARQUET_PATH, PROJECT_ROOT


SAMPLES_DIR = PROJECT_ROOT / "application" / "samples"


SAMPLES = {
    "indie_cafe": {
        "title": "Indie Cafe Sunday",
        "filter_genres": ["chill", "indie", "indie-pop", "acoustic",
                          "singer-songwriter", "songwriter", "folk", "jazz"],
        "n": 25,
        "seed": 11,
    },
    "workout_beast": {
        "title": "Workout Beast Mode",
        "filter_genres": ["edm", "hip-hop", "electronic", "house", "club",
                          "hardstyle", "drum-and-bass", "techno"],
        "n": 25,
        "seed": 22,
    },
    "vinyl_sunday": {
        "title": "Vinyl Sunday Classics",
        "filter_genres": ["jazz", "classical", "blues", "soul", "piano",
                          "bluegrass", "rock-n-roll", "country"],
        "n": 25,
        "seed": 33,
    },
}


KEEP_COLS = (
    ["track_id", "track_name", "artists", "track_genre"]
    + FEATURE_COLS
)


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_PARQUET_PATH)

    for sid, spec in SAMPLES.items():
        pool = df[df["track_genre"].isin(spec["filter_genres"])]
        if len(pool) < spec["n"]:
            print(f"[warn] only {len(pool)} rows match {sid}, expected {spec['n']}")
        sample = pool.sample(n=min(spec["n"], len(pool)), random_state=spec["seed"])
        out = sample[KEEP_COLS].reset_index(drop=True)
        path = SAMPLES_DIR / f"{sid}.csv"
        out.to_csv(path, index=False)
        print(f"[save] {path.name}  ({len(out)} tracks - {spec['title']})")


if __name__ == "__main__":
    main()
