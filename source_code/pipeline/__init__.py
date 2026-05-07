"""SonicDNA pipeline package.

Modules:
    preprocess: load raw CSV -> cleaned parquet + scaler
    cluster: KMeans for mood (k=8) and era anchor (k=12) clustering
    moodprint: render the unique polar-coordinate music DNA artwork
    mbti: 4-axis -> 16-class music personality mapping
    parallel_universe: project user playlist into era/scene anchors
    recommender: cosine similarity Top-N with diversity constraints
"""

from .config import FEATURE_COLS, RAW_CSV_PATH, PROCESSED_PARQUET_PATH

__all__ = ["FEATURE_COLS", "RAW_CSV_PATH", "PROCESSED_PARQUET_PATH"]
