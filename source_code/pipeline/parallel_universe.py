"""Parallel Universe Playlists.

We pre-define three "universes" — each is a sub-population of the
library defined by a curated set of granular Spotify genres. For a
given user playlist we:

    1. Compute the user's mean embedding ``u`` in z-scored space.
    2. Compute each universe's centroid ``a`` (mean of its tracks).
    3. Project the user toward the universe along a straight line:
           ``projected = u + alpha * (a - u)``
       This keeps the user's personal style but warps it toward the
       universe so the recommendations feel like a believable
       "what if you grew up listening to ____" experiment.
    4. Run cosine similarity recommendation **inside** that universe's
       track pool, reusing ``recommender.recommend`` via the
       ``library_subset_mask`` knob.

Universes (3 hand-picked for high contrast):
    - Neon Synthwave Drive : synth-pop / electronic / disco / electro
    - Lo-fi Study Den      : chill / ambient / jazz / piano / study / sleep
    - Mosh Pit Riot        : hard-rock / punk-rock / metal / grunge / ...

Public API:
    list_universes() -> list[Universe]
    project_into(playlist_df, library_df, universe_id, top_n=10) -> dict
"""
from __future__ import annotations

from dataclasses import dataclass, field

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .config import FEATURE_COLS, SCALER_PATH


@dataclass
class Universe:
    id: str
    name_en: str
    name_zh: str
    tagline_en: str
    tagline_zh: str
    genres: list[str]
    color: str
    emoji: str = ""

    def name(self, lang: str = "en") -> str:
        return self.name_zh if lang == "zh" else self.name_en

    def tagline(self, lang: str = "en") -> str:
        return self.tagline_zh if lang == "zh" else self.tagline_en


UNIVERSES: list[Universe] = [
    Universe(
        id="synthwave",
        name_en="Neon Synthwave Drive",
        name_zh="霓虹电子之夜",
        tagline_en=("What if you grew up in a parallel universe that's "
                    "always 2 a.m., neon-lit, and on the highway?"),
        tagline_zh="如果你穿越到一个永远在午夜霓虹中开车的平行宇宙",
        genres=["synth-pop", "electronic", "electro", "disco", "new-age",
                "house", "deep-house", "progressive-house", "chicago-house",
                "edm"],
        color="#FF4DB8",
    ),
    Universe(
        id="lofi",
        name_en="Lo-fi Study Den",
        name_zh="深夜书桌",
        tagline_en=("What if you exiled yourself to a writing den with "
                    "nothing but coffee, rain, and a piano?"),
        tagline_zh="如果你把自己流放到一个只剩咖啡、雨声和钢琴的写作间",
        genres=["chill", "ambient", "jazz", "piano", "study", "sleep",
                "acoustic", "singer-songwriter", "songwriter", "new-age"],
        color="#5BA8FF",
    ),
    Universe(
        id="moshpit",
        name_en="Mosh Pit Riot",
        name_zh="现场暴动",
        tagline_en=("What if you were dropped into an underground live "
                    "house where the crowd never stops surfing?"),
        tagline_zh="如果你被丢进一个永不停歇、Crowdsurfing 不停的地下 Live House",
        genres=["hard-rock", "punk-rock", "metal", "heavy-metal",
                "metalcore", "grunge", "hardcore", "death-metal",
                "black-metal", "punk", "industrial"],
        color="#FF4F4F",
    ),
]


UNIVERSES_BY_ID: dict[str, Universe] = {u.id: u for u in UNIVERSES}


def list_universes() -> list[Universe]:
    return UNIVERSES


def _scaled_columns() -> list[str]:
    return [f"{c}_z" for c in FEATURE_COLS]


def build_anchor_pools(library_df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return a {universe_id: bool mask} dict over library rows."""
    pools: dict[str, pd.Series] = {}
    for u in UNIVERSES:
        mask = library_df["track_genre"].isin(u.genres)
        pools[u.id] = mask
    return pools


def universe_centroid(library_df: pd.DataFrame, universe_id: str) -> np.ndarray:
    mask = library_df["track_genre"].isin(UNIVERSES_BY_ID[universe_id].genres)
    sub = library_df.loc[mask, _scaled_columns()].to_numpy(dtype=np.float64)
    if len(sub) == 0:
        raise ValueError(f"No tracks fall into universe {universe_id!r}")
    return sub.mean(axis=0)


def project_into(
    playlist_df: pd.DataFrame,
    library_df: pd.DataFrame,
    universe_id: str,
    top_n: int = 10,
    alpha: float = 0.7,
    max_per_artist: int = 1,
    max_per_genre: int = 4,
    scaler=None,
) -> dict:
    """Recommend ``top_n`` tracks inside the universe, biased by user taste.

    Returns a dict with:
        universe : Universe object
        projected_z : np.ndarray of length 9 (the warped user vector)
        recommendations : DataFrame
    """
    if universe_id not in UNIVERSES_BY_ID:
        raise ValueError(f"Unknown universe {universe_id!r}")
    if scaler is None:
        scaler = joblib.load(SCALER_PATH)

    z_cols = _scaled_columns()

    # 1. user embedding
    raw = playlist_df[FEATURE_COLS].to_numpy(dtype=np.float64)
    z = scaler.transform(raw)
    user_vec = z.mean(axis=0)                                          # (9,)

    # 2. universe centroid
    anchor_vec = universe_centroid(library_df, universe_id)            # (9,)

    # 3. linear-interp projection
    projected = user_vec + alpha * (anchor_vec - user_vec)
    projected = projected.reshape(1, -1)

    # 4. score against universe pool only
    mask = library_df["track_genre"].isin(UNIVERSES_BY_ID[universe_id].genres)
    pool = library_df.loc[mask].reset_index(drop=True)
    if pool.empty:
        return {
            "universe": UNIVERSES_BY_ID[universe_id],
            "projected_z": projected.flatten(),
            "recommendations": pool,
        }

    pool_emb = pool[z_cols].to_numpy(dtype=np.float64)
    sims = cosine_similarity(projected, pool_emb).flatten()

    # exclude user's existing tracks
    if "track_id" in playlist_df.columns:
        exclude_ids = set(playlist_df["track_id"].astype(str))
    else:
        exclude_ids = set()

    order = np.argsort(-sims)
    artist_count: dict[str, int] = {}
    genre_count: dict[str, int] = {}
    picked: list[int] = []

    for idx in order:
        if len(picked) >= top_n:
            break
        row = pool.iloc[idx]
        tid = str(row["track_id"])
        if tid in exclude_ids:
            continue
        primary_artist = str(row["artists"]).split(";")[0].strip()
        if artist_count.get(primary_artist, 0) >= max_per_artist:
            continue
        genre = str(row["track_genre"])
        if genre_count.get(genre, 0) >= max_per_genre:
            continue
        picked.append(int(idx))
        artist_count[primary_artist] = artist_count.get(primary_artist, 0) + 1
        genre_count[genre] = genre_count.get(genre, 0) + 1

    recs = pool.iloc[picked].copy()
    recs["similarity"] = sims[picked]
    recs = recs[
        ["track_id", "track_name", "artists", "track_genre",
         "popularity", "similarity"]
    ].reset_index(drop=True)

    return {
        "universe": UNIVERSES_BY_ID[universe_id],
        "projected_z": projected.flatten(),
        "anchor_z": anchor_vec,
        "user_z": user_vec,
        "recommendations": recs,
    }


def _smoke_test() -> None:
    """For each universe, project the same Pop playlist and print Top-5."""
    from .config import PROCESSED_PARQUET_PATH

    df = pd.read_parquet(PROCESSED_PARQUET_PATH)
    pop_playlist = df[df["meta_genre"] == "Pop"].sample(20, random_state=7)

    print("Pool sizes:")
    for uid, mask in build_anchor_pools(df).items():
        print(f"  {uid:<10s} -> {int(mask.sum()):,} tracks")
    print()

    for u in UNIVERSES:
        result = project_into(pop_playlist, df, u.id, top_n=5)
        print(f"--- {u.name_en} ({u.name_zh}) ---")
        print(f"    {u.tagline_en}")
        print(result["recommendations"].to_string())
        print()


if __name__ == "__main__":
    _smoke_test()
