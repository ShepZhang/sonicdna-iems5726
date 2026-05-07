"""Global CSS styles for SonicDNA."""

import streamlit as st

def inject_global_styles():
    st.markdown(
        """
        <style>
        /* hide streamlit's default top gradient ribbon and toolbar margin */
        [data-testid="stDecoration"] {display:none !important;}
        [data-testid="stHeader"] {background:transparent;}

        /* very subtle radial vignette so the page stops feeling like a slab */
        [data-testid="stAppViewContainer"] > .main {
            background:
                radial-gradient(circle at 18% -10%, rgba(255,77,184,0.07), transparent 45%),
                radial-gradient(circle at 92% 10%, rgba(91,168,255,0.06), transparent 50%),
                radial-gradient(circle at 50% 110%, rgba(159,123,255,0.05), transparent 55%);
        }

        /* shrink the giant default top padding of the main container */
        .block-container {padding-top: 1.2rem !important;}

        /* tabs: bigger labels, more breathing room, animated underline */
        button[role="tab"] {
            font-size: 15px !important;
            padding: 6px 18px !important;
            transition: color .25s ease, transform .2s ease;
        }
        button[role="tab"]:hover {transform: translateY(-1px);}
        button[role="tab"][aria-selected="true"] {color: #FF4DB8 !important;}

        /* dataframes feel less sterile in dark mode */
        [data-testid="stDataFrame"] {
            border: 1px solid #2a2a3a;
            border-radius: 12px;
            overflow: hidden;
        }

        /* download button — pink gradient with hover lift */
        [data-testid="stDownloadButton"] > button {
            background: linear-gradient(135deg, #FF4DB8 0%, #9F7BFF 100%) !important;
            color: white !important;
            border: 0 !important;
            border-radius: 12px !important;
            padding: 10px 16px !important;
            font-weight: 600 !important;
            box-shadow: 0 6px 20px rgba(255,77,184,0.25);
            transition: transform .2s ease, box-shadow .25s ease, filter .2s ease;
        }
        [data-testid="stDownloadButton"] > button:hover {
            transform: translateY(-2px);
            filter: brightness(1.08);
            box-shadow: 0 10px 28px rgba(255,77,184,0.40);
        }

        /* header stripe — gentle gradient flow */
        .sd-stripe {
            display:flex;align-items:center;gap:14px;
            padding:12px 18px;border-radius:14px;
            background: linear-gradient(90deg,
                #15151F 0%, #1d1235 35%, #2a1a4a 60%, #1d1235 85%, #15151F 100%);
            background-size: 220% 100%;
            border:1px solid #2a2a3a;margin-bottom:14px;
            animation: stripe-flow 14s ease-in-out infinite;
        }
        @keyframes stripe-flow {
            0%, 100% { background-position: 0% 50%; }
            50%      { background-position: 100% 50%; }
        }
        .sd-stripe .sd-logo {
            font-size:24px;
            animation: logo-bob 4s ease-in-out infinite;
        }
        @keyframes logo-bob {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-2px); }
        }
        .sd-stripe .sd-title {
            font-size:18px;font-weight:bold;letter-spacing:0.5px;
            background: linear-gradient(90deg, #fff 0%, #FFB7E0 50%, #fff 100%);
            background-size: 200% 100%;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: title-shimmer 6s linear infinite;
        }
        @keyframes title-shimmer {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }
        .sd-stripe .sd-tagline {
            font-size:13px;color:#aaa;margin-left:auto;
        }

        /* segmented-control look for horizontal radios */
        div[role="radiogroup"] > label[data-baseweb="radio"] {
            background:#15151F;border:1px solid #2a2a3a;
            padding:8px 16px;border-radius:10px;margin-right:6px;
            cursor:pointer;transition:all .2s ease;
        }
        div[role="radiogroup"] > label[data-baseweb="radio"]:hover {
            border-color:#FF4DB8;
            transform: translateY(-1px);
        }
        div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
            background:#2a1a4a;border-color:#FF4DB8;
            box-shadow:0 0 0 1px #FF4DB8 inset, 0 6px 20px rgba(255,77,184,0.20);
        }

        /* MoodPrint legend */
        .sd-print-legend {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px 12px;
            margin: 6px 0 4px 0;
            font-size: 11px;
            color: #bbbbcc;
        }
        .sd-print-legend-row {
            display: flex; align-items: center; gap: 8px;
            white-space: nowrap;
        }
        .sd-print-legend .sw {
            width: 14px; height: 8px; border-radius: 2px;
            flex: 0 0 14px;
        }
        .sd-print-legend .lt {
            font-weight: 700; font-family: ui-monospace, monospace;
            width: 12px; text-align: center;
        }

        /* MoodPrint frame: a circular dark stage that hosts the vinyl PNG.
           Added spin animation for visual effect, and a pseudo-element
           for the spectrum equalizer ring. */
        .sd-print-frame {
            position: relative;
            margin: 16px auto 24px auto;
            width: 100%;
            max-width: 480px;
            aspect-ratio: 1 / 1;
            border-radius: 50%;
            background:
                radial-gradient(circle at 30% 30%, rgba(255,77,184,0.16), transparent 60%),
                radial-gradient(circle at 70% 70%, rgba(91,168,255,0.14), transparent 60%),
                #0B0B14;
            box-shadow:
                0 0 0 1px rgba(255,77,184,0.18),
                0 0 50px rgba(255,77,184,0.18),
                inset 0 0 70px rgba(0,0,0,0.6);
            animation: sd-print-breath 7s ease-in-out infinite;
            transition: transform .35s ease;
        }
        
        /* Audio Spectrum Equalizer ring */
        .sd-print-frame::before {
            content: "";
            position: absolute;
            inset: -8px;
            border-radius: 50%;
            background: conic-gradient(
                from 0deg,
                transparent 0%,
                rgba(255, 77, 184, 0.4) 10%,
                transparent 20%,
                rgba(91, 168, 255, 0.4) 30%,
                transparent 40%,
                rgba(159, 123, 255, 0.4) 50%,
                transparent 60%,
                rgba(255, 210, 86, 0.4) 70%,
                transparent 80%,
                rgba(255, 77, 184, 0.4) 90%,
                transparent 100%
            );
            mask-image: repeating-conic-gradient(
                from 0deg,
                #000 0deg,
                #000 2deg,
                transparent 2deg,
                transparent 4deg
            );
            -webkit-mask-image: repeating-conic-gradient(
                from 0deg,
                #000 0deg,
                #000 2deg,
                transparent 2deg,
                transparent 4deg
            );
            animation: sd-spectrum-dance 1.5s ease-in-out infinite alternate, sd-spin 10s linear infinite;
            z-index: -1;
            opacity: 0.8;
            box-shadow: 0 0 20px rgba(255, 77, 184, 0.2);
        }

        @keyframes sd-spectrum-dance {
            0% { transform: scale(1); opacity: 0.6; }
            50% { transform: scale(1.03); opacity: 0.9; }
            100% { transform: scale(0.98); opacity: 0.7; }
        }

        .sd-print-frame:hover { transform: scale(1.015); }
        
        /* Spin the vinyl image */
        .sd-print-frame > img {
            position: absolute; inset: 0;
            width: 100%; height: 100%;
            display: block;
            border-radius: 50%;
            animation: sd-spin 20s linear infinite;
        }
        
        @keyframes sd-spin {
            100% { transform: rotate(360deg); }
        }

        @keyframes sd-print-breath {
            0%, 100% {
                box-shadow:
                    0 0 0 1px rgba(255,77,184,0.18),
                    0 0 50px rgba(255,77,184,0.18),
                    inset 0 0 70px rgba(0,0,0,0.6);
            }
            50% {
                box-shadow:
                    0 0 0 1px rgba(91,168,255,0.32),
                    0 0 90px rgba(91,168,255,0.28),
                    inset 0 0 70px rgba(0,0,0,0.6);
            }
        }

        /* MBTI card with breathing aura */
        .sd-mbti-card {
            background: linear-gradient(135deg,#1d1235,#2a1a4a);
            border-radius: 16px;
            padding: 22px 24px;
            color: white;
            border: 1px solid #6a5acd44;
            animation: mbti-glow 6s ease-in-out infinite;
            transition: transform .25s ease;
        }
        .sd-mbti-card:hover {transform: translateY(-2px);}
        @keyframes mbti-glow {
            0%, 100% {
                box-shadow:
                    0 0 0 1px #6a5acd44,
                    0 0 28px rgba(255,77,184,0.10);
            }
            50% {
                box-shadow:
                    0 0 0 1px rgba(255,77,184,0.45),
                    0 0 50px rgba(255,77,184,0.22);
            }
        }

        /* Universe selected card — subtle accent line slide */
        .sd-uni-card {
            background:#15151F;border-radius:14px;
            padding:18px 22px;margin:6px 0 18px 0;color:white;
            border:1px solid #2a2a3a;
            position:relative; overflow:hidden;
        }
        .sd-uni-card::before {
            content:""; position:absolute; left:0; top:0; bottom:0;
            width:6px; background: var(--accent, #FF4DB8);
            box-shadow: 0 0 18px var(--accent, #FF4DB8);
        }
        .sd-uni-card::after {
            content:""; position:absolute; inset:0;
            background: radial-gradient(
                circle at 0% 50%, var(--accent, #FF4DB8) 0%, transparent 35%);
            opacity: 0.06; pointer-events:none;
        }

        /* generic section title eyebrow */
        .sd-eyebrow {
            font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
            color: #888; margin-bottom: 4px;
        }
        
        /* Starry background effect for PCA plot container */
        .sd-starry-bg {
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: 
                radial-gradient(2px 2px at 20px 30px, #eee, rgba(0,0,0,0)),
                radial-gradient(2px 2px at 40px 70px, #fff, rgba(0,0,0,0)),
                radial-gradient(2px 2px at 50px 160px, #ddd, rgba(0,0,0,0)),
                radial-gradient(2px 2px at 90px 40px, #fff, rgba(0,0,0,0)),
                radial-gradient(2px 2px at 130px 80px, #fff, rgba(0,0,0,0)),
                radial-gradient(2px 2px at 160px 120px, #ddd, rgba(0,0,0,0));
            background-repeat: repeat;
            background-size: 200px 200px;
            animation: sd-twinkle 4s infinite alternate;
            opacity: 0.4;
            z-index: 0;
        }
        
        @keyframes sd-twinkle {
            0% { opacity: 0.2; transform: scale(1); }
            50% { opacity: 0.6; }
            100% { opacity: 0.3; transform: scale(1.02); }
        }

        /* Radar chart neon glow effect for lines. Note: applied generically to SVG paths in radar */
        .js-plotly-plot .polar path.js-line {
            filter: drop-shadow(0px 0px 4px rgba(255, 255, 255, 0.4));
            animation: sd-neon-pulse 3s infinite alternate;
        }
        
        @keyframes sd-neon-pulse {
            0% { filter: drop-shadow(0px 0px 3px rgba(255, 255, 255, 0.3)); }
            100% { filter: drop-shadow(0px 0px 8px rgba(255, 255, 255, 0.7)); }
        }
        
        /* Scatter plot wrapper relative positioning */
        .sd-scatter-wrapper {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            background: #0f0f17;
            border: 1px solid #2a2a3a;
            padding: 8px;
        }
        
        /* Make sure plotly chart goes above starry bg */
        .sd-scatter-wrapper .js-plotly-plot {
            position: relative;
            z-index: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
