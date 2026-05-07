"""Parallel Universes Tab for SonicDNA."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pipeline.config import FEATURE_COLS
from pipeline.parallel_universe import list_universes
from i18n import t
from caching import get_cached_projection

def render_universe(lang: str, playlist_df: pd.DataFrame, library: pd.DataFrame, scaler):
    st.markdown(f"### {t(lang, 'uni_h')}")
    st.caption(t(lang, "uni_caption"))

    universes = list_universes()
    universe_id_to_obj = {u.id: u for u in universes}
    label_to_id = {u.name(lang): u.id for u in universes}

    chosen_label = st.radio(
        t(lang, "uni_pick"),
        options=list(label_to_id.keys()),
        horizontal=True,
        label_visibility="collapsed",
    )
    chosen = universe_id_to_obj[label_to_id[chosen_label]]

    st.markdown(
        f"""
<div class="sd-uni-card" style="--accent:{chosen.color};">
  <div style="font-size:22px;font-weight:bold;color:{chosen.color};
              letter-spacing:0.5px;position:relative;">
    {chosen.name(lang)}
  </div>
  <div style="font-size:13.5px;color:#bbb;margin-top:6px;line-height:1.5;
              position:relative;">
    {chosen.tagline(lang)}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner(t(lang, "spinner_projecting", name=chosen.name(lang))):
        result = get_cached_projection(playlist_df, library, chosen.id, scaler)
        
    recs_u = result["recommendations"].copy()

    col_recs, col_radar = st.columns([1.05, 1])

    with col_recs:
        st.markdown(f"#### {t(lang, 'uni_recs_h')}")
        if recs_u.empty:
            st.warning("Universe pool is empty for this filter.")
        else:
            recs_u["similarity"] = recs_u["similarity"].round(3)
            st.dataframe(
                recs_u[["track_name", "artists", "track_genre", "similarity"]],
                use_container_width=True,
                hide_index=True,
                height=460,
                column_config={
                    "track_name": st.column_config.TextColumn(
                        "track_name", width="large",
                    ),
                    "artists": st.column_config.TextColumn(
                        "artists", width="medium",
                    ),
                    "track_genre": st.column_config.TextColumn(
                        "track_genre", width="small",
                    ),
                    "similarity": st.column_config.NumberColumn(
                        "similarity", format="%.3f", width="small",
                    ),
                },
            )

    with col_radar:
        st.markdown(f"#### {t(lang, 'uni_radar_h')}")
        user_vec = np.asarray(result["user_z"])
        anchor_vec = np.asarray(result["anchor_z"])
        proj_vec = np.asarray(result["projected_z"])
        feats_loop = FEATURE_COLS + [FEATURE_COLS[0]]
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(
            r=anchor_vec.tolist() + [float(anchor_vec[0])],
            theta=feats_loop,
            fill="toself",
            line=dict(color=chosen.color),
            opacity=0.55,
            name=t(lang, "uni_legend_anchor"),
        ))
        radar.add_trace(go.Scatterpolar(
            r=user_vec.tolist() + [float(user_vec[0])],
            theta=feats_loop,
            line=dict(color="#cccccc", dash="dot"),
            name=t(lang, "uni_legend_user"),
        ))
        radar.add_trace(go.Scatterpolar(
            r=proj_vec.tolist() + [float(proj_vec[0])],
            theta=feats_loop,
            line=dict(color="#FFD256", width=2.5),
            name=t(lang, "uni_legend_proj"),
        ))
        radar.update_layout(
            height=460,
            paper_bgcolor="rgba(0,0,0,0)",
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    range=[-2, 2],
                    visible=True,
                    tickfont=dict(color="#aaa", size=10),
                    gridcolor="#2a2a3a",
                ),
                angularaxis=dict(
                    tickfont=dict(color="#dcdce6", size=11),
                    gridcolor="#2a2a3a",
                ),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                font=dict(color="#dcdce6", size=11),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=20, r=20, t=20, b=40),
        )
        st.plotly_chart(radar, use_container_width=True)
