"""Insights Tab for SonicDNA."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pipeline.config import FEATURE_COLS
from i18n import t

def render_insights(lang: str, playlist_df: pd.DataFrame, mp_stats, library: pd.DataFrame, scaler, pca, cluster_names_dict: dict):
    st.markdown(f"### {t(lang, 'ins_h')}")

    user_z = scaler.transform(playlist_df[FEATURE_COLS].to_numpy())
    user_pca = pca.transform(user_z)

    zoom_to_user = st.toggle(
        t(lang, "ins_zoom_label"),
        value=True,
        help="Re-frame the scatter around your tracks; turn off to see "
             "the full library."
        if lang == "en" else "把视图缩放到你的歌单附近；关闭后查看全曲库地图。",
    )

    sample_lib = library.sample(n=min(8000, len(library)), random_state=0)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=sample_lib["pca_x"], y=sample_lib["pca_y"],
        mode="markers",
        marker=dict(size=3, color=sample_lib["mood_cluster"],
                    colorscale="Spectral", opacity=0.30),
        text=sample_lib["meta_genre"],
        hovertemplate="<b>%{text}</b><br>(%{x:.2f}, %{y:.2f})<extra></extra>",
        name=t(lang, "ins_legend_lib"),
    ))
    fig.add_trace(go.Scattergl(
        x=user_pca[:, 0], y=user_pca[:, 1],
        mode="markers",
        marker=dict(size=12, color="#fff",
                    line=dict(color="#FF4DB8", width=2)),
        name=t(lang, "ins_legend_user"),
    ))

    layout_kwargs: dict = dict(
        height=520,
        title=dict(
            text=t(lang, "ins_pca_title"),
            font=dict(size=14, color="#dcdce6"),
        ),
        xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)",
        yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)",
        legend=dict(
            orientation="h", yanchor="top", y=-0.08,
            font=dict(color="#dcdce6", size=12),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(
            color="#dcdce6",
            title_font=dict(size=13),
            tickfont=dict(size=11),
            gridcolor="#1f1f2a", zerolinecolor="#2a2a3a",
        ),
        yaxis=dict(
            color="#dcdce6",
            title_font=dict(size=13),
            tickfont=dict(size=11),
            gridcolor="#1f1f2a", zerolinecolor="#2a2a3a",
        ),
    )

    if zoom_to_user and user_pca.shape[0] > 0:
        ux_min, ux_max = float(user_pca[:, 0].min()), float(user_pca[:, 0].max())
        uy_min, uy_max = float(user_pca[:, 1].min()), float(user_pca[:, 1].max())
        x_pad = max(1.5, 0.6 * (ux_max - ux_min))
        y_pad = max(1.5, 0.6 * (uy_max - uy_min))
        layout_kwargs["xaxis"]["range"] = [ux_min - x_pad, ux_max + x_pad]
        layout_kwargs["yaxis"]["range"] = [uy_min - y_pad, uy_max + y_pad]

    fig.update_layout(**layout_kwargs)
    
    # Wrap plotly chart in a div that contains the starry background
    st.markdown('<div class="sd-scatter-wrapper"><div class="sd-starry-bg"></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"#### {t(lang, 'ins_radar_h')}")
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(
            r=mp_stats.mean_z.tolist() + [mp_stats.mean_z[0]],
            theta=FEATURE_COLS + [FEATURE_COLS[0]],
            fill="toself",
            line=dict(color="#FF4DB8"),
            name="Your taste",
        ))
        radar.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    range=[-2, 2], visible=True,
                    tickfont=dict(color="#aaa", size=10),
                    gridcolor="#2a2a3a",
                ),
                angularaxis=dict(
                    tickfont=dict(color="#dcdce6", size=11),
                    gridcolor="#2a2a3a",
                ),
            ),
            showlegend=False,
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=10, b=20),
        )
        st.plotly_chart(radar, use_container_width=True)

    with col_b:
        st.markdown(f"#### {t(lang, 'ins_donut_h')}")
        labels_d = [cluster_names_dict.get(i, f"C{i}") for i in range(8)]
        donut = go.Figure(go.Pie(
            labels=labels_d,
            values=mp_stats.cluster_dist.tolist(),
            hole=0.55,
            textfont=dict(color="#fff", size=11),
        ))
        donut.update_layout(
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="v", x=1.0, y=0.5,
                        font=dict(color="#dcdce6", size=11)),
        )
        st.plotly_chart(donut, use_container_width=True)
