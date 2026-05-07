"""MoodPrint: a vinyl-record style data visualization of a playlist.

The print encodes three pieces of information in concentric layers:

    Layer 0  faint vinyl grooves              -- decoration only
    Layer 1  9 feature tracks (inner -> outer) -- one per audio feature.
             Arc length, alpha and width all scale with how strongly the
             playlist exceeds the library mean on that feature.
    Layer 2  outer mood-cluster ring           -- 8 wedges whose angular
             span is proportional to mood-cluster occupancy.
    Layer 3  center label                      -- SONICDNA, n tracks, seed
    Layer 4  bottom-right legend                -- 9 swatch+letter+name rows

Strength mapping (per feature, given z-score `z`):

    strength = clip((z + 2) / 4, 0, 1)         # squashes z in [-2, 2] -> [0, 1]
    arc_deg  = strength * 300                  # leaves a 60-degree gap so 0 vs full is readable
    alpha    = 0.25 + strength * 0.65
    width    = 0.022 + strength * 0.018         # in normalized radius units

Public API (unchanged from before):
    aggregate_playlist(df) -> MoodPrintStats
    render_moodprint(stats) -> bytes (PNG)
"""
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Wedge

from .config import (
    FEATURE_COLS,
    MODELS_DIR,
    MOOD_K,
    MOOD_KMEANS_PATH,
    SCALER_PATH,
)


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

# Three-color family palette. Within each family the rings are slightly
# different shades so adjacent rings are still distinguishable, but the
# overall print reads as a coherent piece (pink top, purple middle,
# blue bottom of the spectrum).
FEATURE_HUES: dict[str, str] = {
    "danceability":     "#FF4DB8",  # pink
    "energy":           "#FF6F8E",  # warm pink
    "valence":          "#FF9B61",  # peachy pink

    "acousticness":     "#9F7BFF",  # violet
    "instrumentalness": "#7B6BFF",  # indigo
    "liveness":         "#A66BFF",  # purple

    "speechiness":      "#5BA8FF",  # sky blue
    "tempo":            "#3DC8FF",  # cyan
    "popularity":       "#B8C0FF",  # silver-blue
}

# Outer ring palette; index = mood-cluster id.
CLUSTER_HUES = [
    "#FF6F8E", "#FF9B61", "#FFD256", "#7AC74F",
    "#3DC8FF", "#5BA8FF", "#9F7BFF", "#FF6BB5",
]

BG_COLOR = "#0B0B14"


# ---------------------------------------------------------------------------
# Stats dataclass + aggregator (unchanged contract, kept stable for callers)
# ---------------------------------------------------------------------------

@dataclass
class MoodPrintStats:
    """Aggregated statistics computed from a user playlist."""
    mean_z: np.ndarray            # shape (9,)
    cluster_dist: np.ndarray      # shape (MOOD_K,)
    n_tracks: int
    seed_hex: str                 # deterministic 6-char hex for the seed line
    mbti_code: str = ""           # optional - not drawn, kept for back-compat


def _seed_color(mean_z: np.ndarray, cluster_dist: np.ndarray) -> str:
    sig = np.concatenate([mean_z.round(3), cluster_dist.round(3)])
    digest = hashlib.sha1(sig.tobytes()).hexdigest()
    r = max(80, int(digest[0:2], 16))
    g = max(80, int(digest[2:4], 16))
    b = max(80, int(digest[4:6], 16))
    return f"#{r:02X}{g:02X}{b:02X}"


def aggregate_playlist(
    playlist_df: pd.DataFrame,
    scaler=None,
    mood_kmeans=None,
) -> MoodPrintStats:
    """Build MoodPrintStats from a user playlist DataFrame."""
    if scaler is None:
        scaler = joblib.load(SCALER_PATH)
    if mood_kmeans is None:
        mood_kmeans = joblib.load(MOOD_KMEANS_PATH)

    missing = [c for c in FEATURE_COLS if c not in playlist_df.columns]
    if missing:
        raise ValueError(
            f"Playlist missing required feature columns: {missing}. "
            f"Expected 9 columns: {FEATURE_COLS}"
        )

    raw = playlist_df[FEATURE_COLS].to_numpy(dtype=np.float64)
    z = scaler.transform(raw)
    mean_z = z.mean(axis=0)

    labels = mood_kmeans.predict(z)
    cluster_dist = np.bincount(labels, minlength=MOOD_K).astype(np.float64)
    cluster_dist /= cluster_dist.sum() if cluster_dist.sum() else 1.0

    return MoodPrintStats(
        mean_z=mean_z,
        cluster_dist=cluster_dist,
        n_tracks=len(playlist_df),
        seed_hex=_seed_color(mean_z, cluster_dist),
    )


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

# Each feature track sits at a specific radius. Inner-to-outer ordering
# matches the FEATURE_COLS iteration order.
RING_RADII = np.linspace(0.30, 0.78, 9)
RING_BASE_W = 0.028   # in normalized radius units
RING_EXTRA_W = 0.020  # added on top of base, scaled by strength

CLUSTER_INNER_R = 0.84
CLUSTER_OUTER_R = 0.91
RIM_INNER_R = 0.925
RIM_OUTER_R = 0.935


def _strength(mean_z: np.ndarray) -> np.ndarray:
    """Map z-score -> [0, 1] strength using the spec formula."""
    return np.clip((mean_z + 2.0) / 4.0, 0.0, 1.0)


def _draw_vinyl_base(ax) -> None:
    """Background disc + a small number of faint grooves to evoke a record.

    Grooves sit BELOW the feature rings; we keep them sparse and dim so
    they read as texture without competing with the data arcs.
    """
    ax.add_patch(Circle((0, 0), 0.96, fc="#08080F", ec="none", zorder=0))
    for r in np.linspace(0.24, 0.82, 24):
        ax.add_patch(Circle(
            (0, 0), r,
            fc="none", ec="#1a1a26",
            lw=0.4, alpha=0.55, zorder=1,
        ))


def _draw_feature_rings(ax, stats: MoodPrintStats) -> None:
    """Nine concentric tracks; each shows a dim baseline and a bright
    data arc whose length / alpha / width encode the feature strength."""
    s = _strength(stats.mean_z)

    # Calculate points per data unit for linewidth scaling
    # Axes span from -1.02 to 1.02, total width = 2.04 in data units.
    # Figure width in points = figwidth_inches * 72
    points_per_data_unit = (ax.figure.get_figwidth() * 72.0) / 2.04

    for i, feat in enumerate(FEATURE_COLS):
        r_center = RING_RADII[i]
        width = RING_BASE_W + RING_EXTRA_W * float(s[i])
        color = FEATURE_HUES[feat]
        lw_pts = width * points_per_data_unit

        # 1) dim baseline groove (full closed ring)
        # Using a Circle patch with an edge color creates a perfect stroke.
        ax.add_patch(Circle(
            (0, 0), r_center,
            fc="none", ec=color,
            lw=lw_pts,
            alpha=0.13, zorder=2,
        ))

        # 2) bright data arc starting from 12 o'clock, going clockwise.
        arc_deg = float(s[i]) * 300.0
        if arc_deg > 0.5:
            arc_alpha = 0.55 + float(s[i]) * 0.40  # 0.55 -> 0.95
            
            theta_arc = np.linspace(np.radians(90.0 - arc_deg), np.radians(90.0), max(20, int(arc_deg)))
            ax.plot(
                r_center * np.cos(theta_arc),
                r_center * np.sin(theta_arc),
                color=color,
                linewidth=lw_pts,
                solid_capstyle="round",
                alpha=arc_alpha,
                zorder=3,
            )


def _draw_cluster_outer(ax, stats: MoodPrintStats) -> None:
    """Outer ring split into 8 wedges by mood-cluster occupancy."""
    band = CLUSTER_OUTER_R - CLUSTER_INNER_R
    width = band

    # Even tracks at zero get a sliver so the ring stays visible.
    weights = stats.cluster_dist + 1e-3
    weights = weights / weights.sum()

    cumulative = 0.0
    for k in range(MOOD_K):
        frac = float(weights[k])
        # Convert 0..1 occupancy along [0, 360 degrees] starting from 12 o'clock.
        theta_a = 90.0 - 360.0 * (cumulative + frac)
        theta_b = 90.0 - 360.0 * cumulative
        cumulative += frac
        color = CLUSTER_HUES[k % len(CLUSTER_HUES)]
        ax.add_patch(Wedge(
            center=(0, 0),
            r=CLUSTER_OUTER_R,
            theta1=theta_a, theta2=theta_b,
            width=width,
            fc=color, ec=BG_COLOR, lw=0.8,
            alpha=0.92, zorder=4,
        ))

    # Outer rim line just for finishing touch.
    ax.add_patch(Wedge(
        center=(0, 0), r=RIM_OUTER_R,
        theta1=0, theta2=360,
        width=RIM_OUTER_R - RIM_INNER_R,
        fc="#2a2a3a", ec="none",
        alpha=0.85, zorder=5,
    ))


def _draw_center_label(ax, stats: MoodPrintStats) -> None:
    """Center hub + three lines: SONICDNA / N TRACKS / seed hex."""
    # Solid darker hub so the label sits cleanly above the inner grooves.
    ax.add_patch(Circle((0, 0), 0.225, fc="#0E0E18", ec="#2a2a3a",
                        lw=0.8, zorder=6))
    # Pin hole to suggest a real record spindle.
    ax.add_patch(Circle((0, 0), 0.022, fc="#000000", ec="#2a2a3a",
                        lw=0.6, zorder=7))

    # Letter spacing simulated with thin spaces (\u2009).
    title = "S\u2009O\u2009N\u2009I\u2009C\u2009D\u2009N\u2009A"
    n_line = f"{stats.n_tracks} TRACKS"
    seed_line = f"seed {stats.seed_hex.lower()}"

    ax.text(0, 0.135, title,
            ha="center", va="center",
            fontsize=11, fontweight="bold",
            color="#dcdce6", family="DejaVu Sans",
            zorder=8)
    ax.text(0, 0.080, n_line,
            ha="center", va="center",
            fontsize=8, fontweight="bold",
            color="#FFD256", family="DejaVu Sans",
            zorder=8)
    ax.text(0, 0.045, seed_line,
            ha="center", va="center",
            fontsize=7,
            color="#888899", family="monospace",
            zorder=8)


FEATURE_LETTER_LABELS: dict[str, tuple[str, str]] = {
    "danceability":     ("D", "Danceability"),
    "energy":           ("E", "Energy"),
    "valence":          ("V", "Valence"),
    "acousticness":     ("A", "Acousticness"),
    "instrumentalness": ("I", "Instrumentalness"),
    "liveness":         ("L", "Liveness"),
    "speechiness":      ("S", "Speechiness"),
    "tempo":            ("T", "Tempo"),
    "popularity":       ("P", "Popularity"),
}
"""Letter + display-name mapping for the 9 feature rings.

The PNG itself stays decoration-free; consumers (Streamlit UI, report)
render this legend in HTML next to the print so it remains readable
regardless of the figure size.
"""


# ---------------------------------------------------------------------------
# Main render entry point
# ---------------------------------------------------------------------------

def render_moodprint(
    stats: MoodPrintStats,
    size_px: int = 1024,
    show_title: bool = False,    # kept for back-compat, no longer used
    transparent: bool = True,    # kept for back-compat
) -> bytes:
    """Render the MoodPrint as transparent PNG bytes.

    The resulting image is a 'vinyl record' style data visualization
    where every visible element corresponds to a real number from the
    user's playlist (no purely decorative animation, no fictional
    spectrum). Drop it into any container; the figure background is
    transparent so the page color shows through outside the disc.
    """
    dpi = 128
    fig_size = size_px / dpi
    fig = plt.figure(
        figsize=(fig_size, fig_size), dpi=dpi,
        facecolor="none" if transparent else BG_COLOR,
    )
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(-1.02, 1.02)
    ax.set_ylim(-1.02, 1.02)
    ax.set_aspect("equal")
    ax.axis("off")

    _draw_vinyl_base(ax)
    _draw_feature_rings(ax, stats)
    _draw_cluster_outer(ax, stats)
    _draw_center_label(ax, stats)

    buf = io.BytesIO()
    fig.savefig(
        buf, format="png",
        facecolor="none" if transparent else BG_COLOR,
        transparent=transparent,
    )
    plt.close(fig)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Smoke test (writes one PNG per canned playlist for visual verification)
# ---------------------------------------------------------------------------

def _smoke_test() -> None:
    from .config import PROCESSED_PARQUET_PATH

    df = pd.read_parquet(PROCESSED_PARQUET_PATH)
    samples = {
        "rock":  df[df["meta_genre"] == "Rock"].sample(20, random_state=1),
        "chill": df[df["meta_genre"] == "Chill"].sample(20, random_state=2),
        "pop":   df[df["meta_genre"] == "Pop"].sample(20, random_state=3),
    }

    out_dir = MODELS_DIR.parent / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    for tag, sample in samples.items():
        stats = aggregate_playlist(sample)
        png = render_moodprint(stats)
        out = out_dir / f"moodprint_smoke_{tag}.png"
        out.write_bytes(png)
        s = _strength(stats.mean_z)
        print(f"[smoke] {tag}: seed={stats.seed_hex} n={stats.n_tracks} "
              f"png={len(png):,}B")
        for feat, z, st_ in zip(FEATURE_COLS, stats.mean_z, s):
            print(f"           {feat:<18s} z={z:+.2f}  s={st_:.2f}  "
                  f"arc={st_*300:5.1f} deg")
        print()


if __name__ == "__main__":
    _smoke_test()
