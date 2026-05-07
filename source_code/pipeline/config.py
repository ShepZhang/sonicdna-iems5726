"""Project-wide path & feature configuration.

Keeping these in one place lets the Streamlit app, notebooks, and
pipeline scripts agree on file locations and column names.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "source_code"
DATA_RAW_DIR = SOURCE_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = SOURCE_ROOT / "data" / "processed"
MODELS_DIR = SOURCE_ROOT / "models"

RAW_CSV_PATH = DATA_RAW_DIR / "dataset.csv"
PROCESSED_PARQUET_PATH = DATA_PROCESSED_DIR / "tracks_clean.parquet"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
MOOD_KMEANS_PATH = MODELS_DIR / "kmeans_mood.pkl"
ANCHOR_KMEANS_PATH = MODELS_DIR / "kmeans_anchor.pkl"
MBTI_TABLE_PATH = MODELS_DIR / "mbti_thresholds.json"
ANCHORS_PATH = MODELS_DIR / "anchors.pkl"

# 9-dim audio feature space we model the entire project on.
FEATURE_COLS: list[str] = [
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
    "tempo",
    "popularity",
]

MOOD_K = 8
ANCHOR_K = 12

RANDOM_STATE = 42
