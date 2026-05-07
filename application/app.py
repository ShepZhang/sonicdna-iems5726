"""SonicDNA Streamlit application.

Run locally:
    cd application
    streamlit run app.py

The app loads the trained models + processed library produced by
``source_code/pipeline``. We add the pipeline package to ``sys.path``
at import time so the same modules drive both notebooks and this UI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

# --- make the pipeline package importable ----------------------------------
APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent
SOURCE_ROOT = PROJECT_ROOT / "source_code"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from pipeline.config import (  # noqa: E402
    FEATURE_COLS,
    MODELS_DIR,
    MOOD_KMEANS_PATH,
    PROCESSED_PARQUET_PATH,
    SCALER_PATH,
)
from pipeline.mbti import attach_track_axes, classify  # noqa: E402
from pipeline.moodprint import aggregate_playlist, render_moodprint  # noqa: E402
from i18n import t  # noqa: E402

# Local components
from styles import inject_global_styles
from components.sidebar import render_sidebar, load_sample
from tabs.dashboard import render_dashboard
from tabs.universe import render_universe
from tabs.insights import render_insights
from tabs.about import render_about


# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SonicDNA · Music Personality Mirror",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject CSS and animations
inject_global_styles()


# --- caching models & library ----------------------------------------------

@st.cache_resource(show_spinner=False)
def load_models():
    scaler = joblib.load(SCALER_PATH)
    mood_km = joblib.load(MOOD_KMEANS_PATH)
    pca = joblib.load(MODELS_DIR / "pca.pkl")
    return scaler, mood_km, pca

@st.cache_data(show_spinner=False)
def load_library() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED_PARQUET_PATH)
    df = attach_track_axes(df)
    return df

@st.cache_data
def mbti_global_distribution(_library: pd.DataFrame) -> dict[str, int]:
    """Total tracks per MBTI type across the entire library."""
    return _library["mbti_type"].value_counts().to_dict()

@st.cache_data
def cluster_names() -> dict[int, str]:
    raw = json.loads((MODELS_DIR / "mood_cluster_names.json").read_text())
    return {int(k): v for k, v in raw.items()}


# --- cached sample loading wrapper -----------------------------------------

@st.cache_data
def load_sample_wrapper(sample_name: str) -> pd.DataFrame:
    return load_sample(sample_name)


# --- sidebar & layout ------------------------------------------------------

playlist_df, playlist_label, lang = render_sidebar(load_sample_wrapper)

st.markdown(
    f"""
    <div class="sd-stripe">
        <div class="sd-logo">🎧</div>
        <div class="sd-title">SonicDNA</div>
        <div class="sd-tagline">{t(lang, 'stripe_tagline')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if playlist_df is None:
    st.info(t(lang, "info_pick_playlist"))
    st.stop()

missing = [c for c in FEATURE_COLS if c not in playlist_df.columns]
if missing:
    st.error(t(lang, "error_missing_cols", cols=", ".join(missing)))
    st.stop()


# --- shared computations ---------------------------------------------------

with st.spinner(t(lang, "spinner_loading_models")):
    scaler, mood_km, pca = load_models()
with st.spinner(t(lang, "spinner_loading_library")):
    library = load_library()

with st.spinner(t(lang, "spinner_building")):
    mp_stats = aggregate_playlist(playlist_df, scaler=scaler, mood_kmeans=mood_km)
    mbti_result = classify(playlist_df, scaler=scaler)
    mp_stats.mbti_code = mbti_result.code
    moodprint_png = render_moodprint(mp_stats)

mbti_counts = mbti_global_distribution(library)
total_tracks = sum(mbti_counts.values())
your_count = mbti_counts.get(mbti_result.code, 0)
your_pct = 100.0 * your_count / total_tracks if total_tracks else 0.0

sorted_types = sorted(mbti_counts.items(), key=lambda kv: -kv[1])
your_rank = next(
    (i for i, (k, _) in enumerate(sorted_types, 1) if k == mbti_result.code),
    16,
)
rarity_label = (
    "rare" if your_rank > 12 else
    "uncommon" if your_rank > 8 else
    "balanced" if your_rank > 4 else
    "mainstream"
)


# --- tabs routing ----------------------------------------------------------

tab_dash, tab_universe, tab_insights, tab_about = st.tabs([
    t(lang, "tab_dashboard"),
    t(lang, "tab_universe"),
    t(lang, "tab_insights"),
    t(lang, "tab_about"),
])

with tab_dash:
    render_dashboard(
        lang, playlist_df, playlist_label, mp_stats, mbti_result, moodprint_png,
        library, scaler, mbti_counts, your_rank, your_pct, rarity_label
    )

with tab_universe:
    render_universe(lang, playlist_df, library, scaler)

with tab_insights:
    render_insights(
        lang, playlist_df, mp_stats, library, scaler, pca, cluster_names()
    )

with tab_about:
    render_about(lang)
