"""Diversity-aware content-based recommender.

Given a user playlist (rows of audio features) we:

    1. Build a single playlist embedding by averaging z-scored features
    2. Score every candidate track via cosine similarity
    3. Apply diversity constraints to avoid the "all 10 songs are by the
       same artist" failure mode that pure cosine ranking produces.

Constraints (configurable):
    - exclude tracks already in the user playlist (track_id match)
    - at most ``max_per_artist`` tracks per artist  (default 1)
    - at most ``max_per_genre`` tracks per meta_genre (default 3)

Public API:
    recommend(playlist_df, library_df, top_n=10, ...) -> pd.DataFrame
"""
from __future__ import annotations

from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .config import FEATURE_COLS, SCALER_PATH


def _scaled_columns() -> list[str]:
    return [f"{c}_z" for c in FEATURE_COLS]


def _embed_playlist(
    playlist_df: pd.DataFrame, scaler=None,
) -> np.ndarray:
    """Return a single normalized embedding (1 x 9) for the playlist."""
    if scaler is None:
        scaler = joblib.load(SCALER_PATH)
    raw = playlist_df[FEATURE_COLS].to_numpy(dtype=np.float64)
    z = scaler.transform(raw)
    return z.mean(axis=0, keepdims=True)


def recommend(
    playlist_df: pd.DataFrame,
    library_df: pd.DataFrame,
    top_n: int = 10,
    max_per_artist: int = 1,
    max_per_genre: int = 3,
    scaler=None,
    exclude_track_ids: Optional[set[str]] = None,
    library_subset_mask: Optional[np.ndarray] = None,
) -> pd.DataFrame:
    """Recommend ``top_n`` tracks similar to ``playlist_df``.

    Parameters
    ----------
    playlist_df : DataFrame
        Must include the 9 raw audio feature columns.
    library_df : DataFrame
        Must include the 9 z-scored columns plus track_id, track_name,
        artists, meta_genre.
    top_n : int
        Number of recommendations to return.
    max_per_artist : int
        Hard cap to enforce artist-level diversity.
    max_per_genre : int
        Hard cap to enforce meta-genre diversity.
    library_subset_mask : optional bool array
        If provided, only score rows where mask is True. Used by the
        Parallel Universe module to constrain recommendations to a
        specific anchor's track pool.
    """
    z_cols = _scaled_columns()
    needed = z_cols + ["track_id", "track_name", "artists", "meta_genre"]
    missing = [c for c in needed if c not in library_df.columns]
    if missing:
        raise ValueError(f"library_df missing columns: {missing}")

    if library_subset_mask is not None:
        library_df = library_df.loc[library_subset_mask].reset_index(drop=True)

    user_emb = _embed_playlist(playlist_df, scaler=scaler)        # (1, 9)
    lib_emb = library_df[z_cols].to_numpy(dtype=np.float64)        # (N, 9)

    sims = cosine_similarity(user_emb, lib_emb).flatten()          # (N,)

    # Build exclude set (user playlist tracks).
    if exclude_track_ids is None:
        exclude_track_ids = (
            set(playlist_df["track_id"].astype(str))
            if "track_id" in playlist_df.columns else set()
        )

    # Sort indices by similarity desc.
    order = np.argsort(-sims)

    artist_count: dict[str, int] = {}
    genre_count: dict[str, int] = {}
    picked: list[int] = []

    for idx in order:
        if len(picked) >= top_n:
            break
        row = library_df.iloc[idx]
        tid = str(row["track_id"])
        if tid in exclude_track_ids:
            continue
        # First-listed primary artist is used for the diversity cap.
        primary_artist = str(row["artists"]).split(";")[0].strip()
        if artist_count.get(primary_artist, 0) >= max_per_artist:
            continue
        genre = str(row["meta_genre"])
        if genre_count.get(genre, 0) >= max_per_genre:
            continue

        picked.append(int(idx))
        artist_count[primary_artist] = artist_count.get(primary_artist, 0) + 1
        genre_count[genre] = genre_count.get(genre, 0) + 1

    out = library_df.iloc[picked].copy()
    out["similarity"] = sims[picked]
    out = out[
        ["track_id", "track_name", "artists", "track_genre",
         "meta_genre", "popularity", "similarity"]
    ].reset_index(drop=True)
    return out


def _smoke_test() -> None:
    """Pick a 25-song Rock playlist and recommend Top-10 from the library."""
    from .config import PROCESSED_PARQUET_PATH

    df = pd.read_parquet(PROCESSED_PARQUET_PATH)
    rock = df[df["meta_genre"] == "Rock"].sample(25, random_state=42)

    recs = recommend(rock, df, top_n=10)
    print("[smoke] Top-10 recommendations from a Rock playlist:")
    print(recs.to_string())


if __name__ == "__main__":
    _smoke_test()
