"""About Tab for SonicDNA."""

import streamlit as st
from i18n import t

def render_about(lang: str):
    st.markdown(t(lang, "about_body"))
