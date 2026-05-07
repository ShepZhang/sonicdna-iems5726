"""Sidebar component for SonicDNA."""

import pandas as pd
import streamlit as st
from pathlib import Path
from i18n import t

APP_ROOT = Path(__file__).resolve().parent.parent

SAMPLE_OPTIONS = {
    "Indie Cafe Sunday": "indie_cafe",
    "Workout Beast Mode": "workout_beast",
    "Vinyl Sunday Classics": "vinyl_sunday",
}

def load_sample(sample_name: str) -> pd.DataFrame:
    return pd.read_csv(APP_ROOT / "samples" / f"{sample_name}.csv")

def render_sidebar(load_sample_fn):
    """Renders the sidebar and returns (playlist_df, playlist_label, lang).

    The application is English-only; ``lang`` is hard-coded to ``"en"``
    so the existing ``t()`` lookups in shared modules keep working
    without further changes.
    """
    lang = "en"
    st.session_state["lang"] = lang

    with st.sidebar:
        st.markdown("# 🎧 SonicDNA")
        st.caption(t(lang, "app_subtitle"))
        st.divider()

        st.markdown(f"### {t(lang, 'sidebar_step1')}")
        source = st.radio(
            t(lang, "sidebar_source"),
            [t(lang, "sidebar_use_sample"), t(lang, "sidebar_upload")],
            label_visibility="collapsed",
        )

        playlist_df: pd.DataFrame | None = None
        playlist_label = ""

        if source == t(lang, "sidebar_use_sample"):
            choice = st.selectbox(
                t(lang, "sidebar_sample_label"), list(SAMPLE_OPTIONS.keys()),
            )
            playlist_df = load_sample_fn(SAMPLE_OPTIONS[choice])
            playlist_label = choice
        else:
            uploaded = st.file_uploader(
                t(lang, "sidebar_upload_label"),
                type=["csv"],
                help=t(lang, "sidebar_upload_help"),
            )
            if uploaded:
                try:
                    playlist_df = pd.read_csv(uploaded)
                    if playlist_df.empty:
                        raise ValueError("File is empty.")
                    playlist_label = uploaded.name
                except pd.errors.EmptyDataError:
                    st.error("Error: the uploaded CSV is empty.")
                    playlist_df = None
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
                    playlist_df = None

        st.divider()
        st.markdown(f"### {t(lang, 'sidebar_step2')}")
        st.caption(t(lang, "sidebar_tab_blurb"))
        st.divider()
        st.caption(t(lang, "course_footer"))

    return playlist_df, playlist_label, lang
