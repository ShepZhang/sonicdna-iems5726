"""English-only UI strings for SonicDNA.

Use ``t(lang, "key")`` to look up a string. The ``lang`` argument is
kept in the signature so existing callers continue to work, but the
application now ships English copy only -- any value of ``lang`` will
return the English string. Unknown keys fall back to the key itself
so the app never crashes on a missing translation.
"""
from __future__ import annotations

from typing import Literal

Lang = Literal["en"]


STRINGS: dict[str, str] = {
    # --- sidebar ---
    "app_subtitle": "A multi-lens music personality mirror",
    "sidebar_step1": "1. Pick a playlist",
    "sidebar_source": "Playlist source",
    "sidebar_use_sample": "Use a sample",
    "sidebar_upload": "Upload my own CSV",
    "sidebar_sample_label": "Sample",
    "sidebar_upload_label": "Upload CSV with 9 audio features",
    "sidebar_upload_help": (
        "Required columns: track_id, track_name, artists, track_genre + "
        "9 audio features"
    ),
    "sidebar_step2": "2. What's inside",
    "sidebar_tab_blurb": (
        "**Dashboard** — your MoodPrint + Music MBTI\n\n"
        "**Universe** — 3 parallel-universe playlists\n\n"
        "**Insights** — see your taste on a 90k-song map\n\n"
        "**About** — project + model links"
    ),
    "course_footer": "IEMS5726 · Group 43 · Session A",

    # --- shared ---
    "info_pick_playlist": (
        "Pick a sample playlist or upload your own CSV in the sidebar to "
        "get started."
    ),
    "error_missing_cols": (
        "Uploaded CSV is missing required feature columns: {cols}"
    ),
    "spinner_loading_models": "Loading SonicDNA models …",
    "spinner_loading_library": "Loading 89,740-track library …",
    "spinner_building": "Building your SonicDNA …",
    "spinner_scoring": "Scoring 89,740 tracks …",
    "spinner_projecting": "Projecting into {name} …",

    # --- header stripe ---
    "stripe_tagline": "a multi-lens music personality mirror",

    # --- tabs ---
    "tab_dashboard": "Dashboard",
    "tab_universe": "Parallel Universes",
    "tab_insights": "Insights",
    "tab_about": "About",

    # --- dashboard ---
    "dash_loaded": "Loaded **{label}** · {n} tracks · seed `{seed}`",
    "dash_moodprint_h": "Your MoodPrint",
    "dash_download_btn": "⬇  Download MoodPrint as PNG",
    "dash_moodprint_caption": (
        "Each ring is one of 9 audio features (D/E/V/A/I/L/S/T/P). "
        "The brighter and longer the arc, the higher you score on "
        "that feature. The outer band shows your mix across 8 mood "
        "clusters."
    ),
    "dash_mbti_h": "Your Music MBTI",
    "dash_mbti_label": "MUSIC PERSONALITY TYPE",
    "dash_rarity_label": "RARITY",
    "dash_rarity_rank": "rank #{rank}/16 · {pct:.1f}% of library",
    "dash_dist_title": "Distribution across 16 types · your row highlighted",
    "dash_axis_h": "Axis breakdown",
    "dash_recs_h": "Top-10 diversity-aware recommendations",
    "dash_recs_caption": (
        "Cosine similarity over 9 audio features, then filtered to "
        "≤1 track per artist and ≤3 per meta-genre."
    ),

    # --- universe ---
    "uni_h": "Three parallel universes, one taste vector",
    "uni_caption": (
        "Pick a universe below. We project your playlist toward its "
        "centroid (α=0.7), then run cosine recommendation **inside** "
        "that universe's track pool."
    ),
    "uni_pick": "Choose a universe",
    "uni_recs_h": "Top-10 recommendations in this universe",
    "uni_radar_h": "How your taste warps toward this universe",
    "uni_legend_user": "You",
    "uni_legend_anchor": "Universe centroid",
    "uni_legend_proj": "Projected (α=0.7)",

    # --- insights ---
    "ins_h": "Where do you sit on the music map?",
    "ins_pca_title": "PCA 2-D projection · 89,740 tracks",
    "ins_zoom_label": "Zoom to my tracks",
    "ins_legend_lib": "Library",
    "ins_legend_user": "Your tracks",
    "ins_radar_h": "Your 9-axis taste fingerprint",
    "ins_donut_h": "Mood-cluster mix in your playlist",

    # --- about ---
    "about_body": (
        "### About SonicDNA\n\n"
        "A music-taste analyzer built for **IEMS5726 Data Science in "
        "Practice 2025-26 · Session A**. The app turns raw audio "
        "features into three creative outputs:\n\n"
        "1. **MoodPrint** — a unique vinyl-style data visualization where "
        "every concentric ring encodes one of nine audio features and "
        "the outer ring tracks the mood-cluster mix.\n"
        "2. **Music MBTI** — a 4-axis personality reduction over the "
        "9-dim feature space, interpretable as 16 named music types.\n"
        "3. **Parallel Universes** — linear-interpolation projection "
        "from the user's centroid toward 3 hand-curated universe "
        "centroids, then constrained cosine-similarity recommendation "
        "inside each pool.\n\n"
        "#### Data source\n"
        "[Kaggle Spotify Tracks Dataset]"
        "(https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) "
        "(114k tracks de-duplicated to ~90k, 9 audio features).\n\n"
        "#### Stack\n"
        "`pandas`, `numpy`, `scikit-learn`, `matplotlib`, `plotly`, "
        "`streamlit`, deployed via Docker → HuggingFace Spaces.\n\n"
        "#### Pretrained models\n"
        "KMeans (`kmeans_mood.pkl`), StandardScaler (`scaler.pkl`), "
        "PCA (`pca.pkl`) — public download links inside the report PDF.\n\n"
        "#### Why Streamlit instead of Vue + FastAPI?\n"
        "Single-developer, 3-day budget. The pipeline package is fully "
        "decoupled from the UI; swapping Streamlit for the standard "
        "Vue + FastAPI + NGINX stack is a UI replacement only."
    ),
}


def t(lang: Lang | str, key: str, **kwargs) -> str:
    """Look up a UI string. ``lang`` is accepted for backwards
    compatibility but ignored -- the app is English-only.
    """
    s = STRINGS.get(key, key)
    return s.format(**kwargs) if kwargs else s
