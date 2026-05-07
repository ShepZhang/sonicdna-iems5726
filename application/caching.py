"""Caching wrappers for expensive computations."""

import streamlit as st
import pandas as pd
from pipeline.recommender import recommend
from pipeline.parallel_universe import project_into

@st.cache_data(show_spinner=False)
def get_cached_recs(playlist_df: pd.DataFrame, _library: pd.DataFrame, _scaler) -> pd.DataFrame:
    """Cached wrapper for generating diversity-aware recommendations."""
    return recommend(playlist_df, _library, top_n=10, scaler=_scaler)

@st.cache_data(show_spinner=False)
def get_cached_projection(playlist_df: pd.DataFrame, _library: pd.DataFrame, universe_id: str, _scaler) -> dict:
    """Cached wrapper for projecting user taste into a parallel universe."""
    return project_into(playlist_df, _library, universe_id, top_n=10, scaler=_scaler)
