"""Dashboard Tab for SonicDNA."""

import base64
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from pipeline.config import FEATURE_COLS
from pipeline.mbti import TYPE_DESCRIPTIONS
from pipeline.moodprint import FEATURE_HUES, FEATURE_LETTER_LABELS
from i18n import t
from caching import get_cached_recs

def render_dashboard(lang: str, playlist_df: pd.DataFrame, playlist_label: str, mp_stats, mbti_result, moodprint_png: bytes, library: pd.DataFrame, scaler, mbti_counts: dict, your_rank: int, your_pct: float, rarity_label: str):
    st.caption(t(lang, "dash_loaded",
                 label=playlist_label,
                 n=mp_stats.n_tracks,
                 seed=mp_stats.seed_hex.lower()))

    col_print, col_mbti = st.columns([1, 1])

    with col_print:
        st.markdown(f"#### {t(lang, 'dash_moodprint_h')}")

        png_b64 = base64.b64encode(moodprint_png).decode("ascii")
        st.markdown(
            f"""
<div class="sd-print-frame">
    <img src="data:image/png;base64,{png_b64}" alt="SonicDNA MoodPrint" />
</div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label=t(lang, "dash_download_btn"),
            data=moodprint_png,
            file_name=f"sonicdna_{mbti_result.code.lower()}_"
                      f"{mp_stats.seed_hex.replace('#','').lower()}.png",
            mime="image/png",
            use_container_width=True,
        )

        st.caption(t(lang, "dash_moodprint_caption"))

        legend_rows = "".join(
            f'<div class="sd-print-legend-row">'
            f'<span class="sw" style="background:{FEATURE_HUES[f]};"></span>'
            f'<span class="lt" style="color:{FEATURE_HUES[f]};">'
            f'{FEATURE_LETTER_LABELS[f][0]}</span>'
            f'<span>{FEATURE_LETTER_LABELS[f][1]}</span>'
            f'</div>'
            for f in FEATURE_COLS
        )
        st.markdown(
            f'<div class="sd-print-legend">{legend_rows}</div>',
            unsafe_allow_html=True,
        )

    with col_mbti:
        st.markdown(f"#### {t(lang, 'dash_mbti_h')}")
        st.markdown(
            f"""
<div class="sd-mbti-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div class="sd-eyebrow">{t(lang, "dash_mbti_label")}</div>
      <div style="font-size:56px;font-weight:bold;letter-spacing:6px;
                  margin:4px 0;line-height:1;
                  background:linear-gradient(135deg,#fff 0%,#FFB7E0 60%,#9F7BFF 100%);
                  -webkit-background-clip:text;background-clip:text;
                  color:transparent;">
        {mbti_result.code}
      </div>
    </div>
    <div style="text-align:right;">
      <div class="sd-eyebrow">{t(lang, "dash_rarity_label")}</div>
      <div style="font-size:18px;color:#FFD256;font-weight:bold;
                  text-transform:uppercase;letter-spacing:1px;">
        {rarity_label}
      </div>
      <div style="font-size:11px;color:#aaa;margin-top:2px;">
        {t(lang, "dash_rarity_rank", rank=your_rank, pct=your_pct)}
      </div>
    </div>
  </div>
  <div style="font-size:22px;color:#ffd256;margin-top:6px;">
    {mbti_result.name(lang)}
  </div>
  <div style="font-size:14px;line-height:1.7;color:#dcdce6;margin-top:10px;">
    {mbti_result.description(lang)}
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

        dist_df = pd.DataFrame({
            "type": list(TYPE_DESCRIPTIONS.keys()),
            "count": [mbti_counts.get(t_, 0) for t_ in TYPE_DESCRIPTIONS.keys()],
        }).sort_values("count", ascending=True)
        dist_df["color"] = ["#FF4DB8" if t_ == mbti_result.code else "#3a3a4f"
                            for t_ in dist_df["type"]]
        mini = go.Figure(go.Bar(
            x=dist_df["count"], y=dist_df["type"],
            orientation="h",
            marker=dict(color=dist_df["color"]),
            hovertemplate="%{y}: %{x:,} tracks<extra></extra>",
        ))
        mini.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=22, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False,
                       tickfont=dict(size=9, color="#888")),
            yaxis=dict(tickfont=dict(size=10, color="#aaa")),
            title=dict(
                text=t(lang, "dash_dist_title"),
                font=dict(size=11, color="#888"),
                x=0.0, xanchor="left",
            ),
        )
        st.plotly_chart(mini, use_container_width=True)

        st.markdown(f"##### {t(lang, 'dash_axis_h')}")
        axes_df = pd.DataFrame({
            "axis": ["E ⇆ I", "N ⇆ S", "F ⇆ T", "J ⇆ P"],
            "score": [
                mbti_result.axes["EI"],
                mbti_result.axes["NS"],
                mbti_result.axes["FT"],
                mbti_result.axes["JP"],
            ],
        })
        bar = px.bar(
            axes_df, x="score", y="axis", orientation="h",
            color="score", color_continuous_scale="RdBu_r",
            range_color=[-2, 2],
        )
        bar.update_layout(
            height=200, showlegend=False, coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=4, b=4),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickfont=dict(color="#aaa"), zeroline=True,
                       zerolinecolor="#444", showgrid=False),
            yaxis=dict(tickfont=dict(color="#fff", size=14)),
        )
        st.plotly_chart(bar, use_container_width=True)

    st.divider()
    st.markdown(f"#### {t(lang, 'dash_recs_h')}")
    st.caption(t(lang, "dash_recs_caption"))
    with st.spinner(t(lang, "spinner_scoring")):
        recs = get_cached_recs(playlist_df, library, scaler)
        
    if recs.empty:
        st.warning("No recommendations could be produced.")
    else:
        recs_show = recs.copy()
        recs_show["similarity"] = recs_show["similarity"].round(3)
        st.dataframe(
            recs_show.drop(columns=["track_id"]),
            use_container_width=True,
            hide_index=True,
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
