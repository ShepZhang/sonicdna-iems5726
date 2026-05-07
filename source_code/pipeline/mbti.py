"""Music MBTI: a 4-axis personality mapping over 9 audio features.

Each user playlist is reduced to a 4-letter type by sign of four
composite axes:

    E (Extrovert)  vs  I (Introvert)    : energy + danceability
    N (iNtuitive)  vs  S (Sensing)      : acousticness + instrumentalness
    F (Feeling)    vs  T (Thinking)     : valence - 0.5 * speechiness
    J (Judging)    vs  P (Perceiving)   : popularity (mainstream vs niche)

The same axes apply to individual tracks too, which is how we generate
each type's representative song list (we filter the library down to
tracks whose own axes match, then pick the most central ones).

Public API:
    classify(playlist_df) -> MBTIResult
    representative_tracks(library_df, type_code, k=5) -> DataFrame
"""
from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd

from .config import FEATURE_COLS, SCALER_PATH


# Each entry: nickname (en/zh) plus a paragraph in each language.
TYPE_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "ENFJ": {
        "name_en": "Stadium Sun", "name_zh": "万人合唱体",
        "desc_en": "Your playlist is a summer stadium gig: bright, "
                   "high-energy, full of harmonies. You gravitate to songs "
                   "that pull strangers into a group sing-along.",
        "desc_zh": "你的歌单像一场夏日体育场演唱会：高能、明亮、和声充沛。"
                   "你天然会找那些能把陌生人团成一团唱合唱的歌，副歌一来全场起立。",
    },
    "ENFP": {
        "name_en": "Festival Comet", "name_zh": "音乐节彗星",
        "desc_en": "Your ears are always on tour, sweeping from underground "
                   "labels to bright indie cuts. Refuses to be predictable; "
                   "your playlist is a list of secret tracks no one else has.",
        "desc_zh": "你的耳朵永远在路上：从地下小厂牌到独立 indie 都收得齐。"
                   "情绪明亮但又拒绝套路，你的歌单是别人没听过的彩蛋合集。",
    },
    "ENTJ": {
        "name_en": "Power Hour", "name_zh": "高能时刻",
        "desc_en": "You listen like you're commanding a small army: biting "
                   "rhythms, hooks with edges. Mainstream pop is fine — but "
                   "every single track is fuel.",
        "desc_zh": "你听歌像在调度一支军队：节奏咬人、旋律带刀。"
                   "排行榜上的硬核流行你照单全收，但每一首都用来打鸡血。",
    },
    "ENTP": {
        "name_en": "Genre Hacker", "name_zh": "曲风黑客",
        "desc_en": "You hate being defined by a genre: electronica blends "
                   "with jazz and hops to hip-hop. High-speechiness "
                   "experiments are your comfort zone.",
        "desc_zh": "你不喜欢被风格定义：电子混了爵士又跳到 hip-hop。"
                   "speechiness 飙高的实验曲 + 小众探索是你的舒适区。",
    },
    "ESFJ": {
        "name_en": "Block Party Host", "name_zh": "街区派对主人",
        "desc_en": "Your playlist is the BBQ-block-party default: catchy, "
                   "danceable, zero friction. You're the friend who pulls "
                   "everyone onto the dance floor.",
        "desc_zh": "你的播放列表是邻里 BBQ 的标配：抓耳、舞动、零负担。"
                   "永远是身边那个把所有人拉进舞池的 DJ 角色。",
    },
    "ESFP": {
        "name_en": "Neon Headliner", "name_zh": "霓虹头条",
        "desc_en": "You live for the live show: disco, reggaeton, "
                   "high-BPM pop. Your playlist asks one question — "
                   "is it bouncing tonight?",
        "desc_zh": "你为现场而生：迪斯科、reggaeton、高 BPM 流行通通照单全收。"
                   "你的歌单只问一件事：今晚跳得起来吗？",
    },
    "ESTJ": {
        "name_en": "Drive-Time DJ", "name_zh": "通勤 DJ",
        "desc_en": "Efficient listener: every track has to deliver in the "
                   "first 30 seconds. Classic rock and current pop dominate, "
                   "decades-old hits on rotation forever.",
        "desc_zh": "你的歌单效率优先：副歌前奏 30 秒内必须给力。"
                   "经典摇滚和当红 pop 占大头，几十年金曲循环不腻。",
    },
    "ESTP": {
        "name_en": "Mosh Pit Mover", "name_zh": "现场推搡者",
        "desc_en": "You listen to be pushed around: punk, metal, hardcore "
                   "electronica. There are no deep cuts in your library, "
                   "only the next surge you haven't found yet.",
        "desc_zh": "你听歌是为了被推一下：punk、metal、硬核电子。"
                   "discography 里没有冷门，只有还没被你发掘的下一波猛料。",
    },
    "INFJ": {
        "name_en": "Library Mystic", "name_zh": "图书馆神秘客",
        "desc_en": "You listen to atmosphere — the air, the light, the "
                   "rain. Acoustic instrumentals and minimal ambient are "
                   "your long-loop habitat.",
        "desc_zh": "你听的是空气、是光线、是窗外的雨。"
                   "原声器乐 + 极简 ambient 是你长期循环的精神栖息地。",
    },
    "INFP": {
        "name_en": "Bedroom Poet", "name_zh": "卧室诗人",
        "desc_en": "Folk, indie, slowcore, singer-songwriter — you listen "
                   "to other people's diaries. Almost no one shares your "
                   "exact mix because it IS you.",
        "desc_zh": "民谣、indie、慢核、singer-songwriter——你听别人写日记。"
                   "歌单里几乎没有人听过同样的组合，因为它就是你本人。",
    },
    "INTJ": {
        "name_en": "Architect's Score", "name_zh": "建筑师配乐",
        "desc_en": "You pick music like you pick materials: post-rock, IDM, "
                   "neo-classical, every track has structure. Few hits, "
                   "but each one unfolds in three layers.",
        "desc_zh": "你听歌像选材：post-rock、IDM、新古典都讲究结构。"
                   "歌单里很少 hit 单曲，但每一首都能拆出三层音色。",
    },
    "INTP": {
        "name_en": "Lab Pulse", "name_zh": "实验室脉冲",
        "desc_en": "Obsessed with timbre itself: experimental electronica, "
                   "jazz fusion, glitch. Speechiness near zero, "
                   "instrumentalness maxed — you listen to sounds, not words.",
        "desc_zh": "你迷恋音色本身：实验电子、jazz fusion、glitch。"
                   "speechiness 极低、instrumentalness 拉满，你听的是声音不是话。",
    },
    "ISFJ": {
        "name_en": "Café Confidant", "name_zh": "咖啡馆密友",
        "desc_en": "Gentle R&B, bossa, acoustic pop are regulars. Your "
                   "playlist is a never-too-hot latte: anyone can drink it, "
                   "but only you taste the layers.",
        "desc_zh": "温柔的 R&B、bossa、acoustic pop 是你的常客。"
                   "歌单像一杯不烫嘴的拿铁，谁都能喝得下去但只有你懂层次。",
    },
    "ISFP": {
        "name_en": "Velvet Wanderer", "name_zh": "丝绒漫游者",
        "desc_en": "Ambient R&B, city-pop, neo-soul, bedroom indie — your "
                   "playlist forever paces between gentle melancholy and "
                   "low-key romance.",
        "desc_zh": "氛围 R&B、city-pop、neo-soul、bedroom indie……"
                   "你的歌单永远在淡淡的忧郁与浪漫之间踱步。",
    },
    "ISTJ": {
        "name_en": "Vinyl Archivist", "name_zh": "黑胶归档者",
        "desc_en": "Classic rock, jazz, blues, country — the older the "
                   "more reassuring. Your playlist could be a time capsule "
                   "and still hold up decades from now.",
        "desc_zh": "经典摇滚、爵士、blues、country——年代越久你越安心。"
                   "歌单可以做时间胶囊，几十年后依旧成立。",
    },
    "ISTP": {
        "name_en": "Late-Night Coder", "name_zh": "深夜代码工",
        "desc_en": "Lo-fi beats, minimal techno, deep house carry your "
                   "workflow. Music can't be loud — but it must have a "
                   "steady rhythm to keep you locked in.",
        "desc_zh": "lo-fi beats、minimal techno、deep house 撑起你的工作流。"
                   "歌不能太喧闹，但必须有一条结实的节奏让你专注下去。",
    },
}


@dataclass
class MBTIResult:
    code: str                  # e.g. "INFP"
    name_en: str
    name_zh: str
    desc_en: str
    desc_zh: str
    axes: dict[str, float]     # raw composite scores per axis

    def name(self, lang: str = "en") -> str:
        return self.name_zh if lang == "zh" else self.name_en

    def description(self, lang: str = "en") -> str:
        return self.desc_zh if lang == "zh" else self.desc_en


def _scaled_columns() -> list[str]:
    return [f"{c}_z" for c in FEATURE_COLS]


def _axes_from_z(z: np.ndarray) -> dict[str, float]:
    """Compute four composite axis scores from a z-scored matrix.

    All inputs are already z-scored, so axis sign is meaningful: > 0
    pushes toward the first letter (E/N/F/J), < 0 toward the second.
    """
    cols = {c: i for i, c in enumerate(FEATURE_COLS)}
    if z.ndim == 1:
        z = z[None, :]
    means = z.mean(axis=0)

    return {
        "EI": float(means[cols["energy"]] + means[cols["danceability"]]),
        "NS": float(means[cols["acousticness"]] + means[cols["instrumentalness"]]),
        "FT": float(means[cols["valence"]] - 0.5 * means[cols["speechiness"]]),
        "JP": float(means[cols["popularity"]]),
    }


def _code_from_axes(axes: dict[str, float]) -> str:
    return (
        ("E" if axes["EI"] > 0 else "I")
        + ("N" if axes["NS"] > 0 else "S")
        + ("F" if axes["FT"] > 0 else "T")
        + ("J" if axes["JP"] > 0 else "P")
    )


def classify(
    playlist_df: pd.DataFrame, scaler=None,
) -> MBTIResult:
    """Classify a user playlist into one of 16 music personality types."""
    if scaler is None:
        scaler = joblib.load(SCALER_PATH)

    raw = playlist_df[FEATURE_COLS].to_numpy(dtype=np.float64)
    z = scaler.transform(raw)
    axes = _axes_from_z(z)
    code = _code_from_axes(axes)
    info = TYPE_DESCRIPTIONS[code]
    return MBTIResult(
        code=code,
        name_en=info["name_en"],
        name_zh=info["name_zh"],
        desc_en=info["desc_en"],
        desc_zh=info["desc_zh"],
        axes=axes,
    )


def attach_track_axes(library_df: pd.DataFrame) -> pd.DataFrame:
    """Add per-track axis columns and 4-letter type to the library.

    This is computed once and cached on the library DataFrame; the
    Streamlit app calls it via ``st.cache_data``.
    """
    z = library_df[_scaled_columns()].to_numpy(dtype=np.float64)
    out = library_df.copy()
    cols = {c: i for i, c in enumerate(FEATURE_COLS)}
    out["axis_EI"] = z[:, cols["energy"]] + z[:, cols["danceability"]]
    out["axis_NS"] = z[:, cols["acousticness"]] + z[:, cols["instrumentalness"]]
    out["axis_FT"] = z[:, cols["valence"]] - 0.5 * z[:, cols["speechiness"]]
    out["axis_JP"] = z[:, cols["popularity"]]
    # numpy's char arrays don't broadcast with `+`; build via pandas Series.
    ei = pd.Series(np.where(out["axis_EI"] > 0, "E", "I"), index=out.index)
    ns = pd.Series(np.where(out["axis_NS"] > 0, "N", "S"), index=out.index)
    ft = pd.Series(np.where(out["axis_FT"] > 0, "F", "T"), index=out.index)
    jp = pd.Series(np.where(out["axis_JP"] > 0, "J", "P"), index=out.index)
    out["mbti_type"] = ei.str.cat([ns, ft, jp])
    return out


def representative_tracks(
    library_df: pd.DataFrame,
    type_code: str,
    k: int = 5,
) -> pd.DataFrame:
    """Return ``k`` tracks whose individual MBTI assignment matches the type.

    Picks tracks that are deepest into their quadrant (largest sum of
    absolute axis values in the right direction) so they are unambiguous
    representatives, not borderline cases.
    """
    if "mbti_type" not in library_df.columns:
        library_df = attach_track_axes(library_df)

    matched = library_df[library_df["mbti_type"] == type_code].copy()
    if matched.empty:
        return matched

    # Compute "type strength" = how strongly each axis agrees with the code.
    sign = np.array([
        1 if type_code[0] == "E" else -1,
        1 if type_code[1] == "N" else -1,
        1 if type_code[2] == "F" else -1,
        1 if type_code[3] == "J" else -1,
    ])
    axes_arr = matched[["axis_EI", "axis_NS", "axis_FT", "axis_JP"]].to_numpy()
    matched["type_strength"] = (axes_arr * sign).sum(axis=1)

    return (
        matched.sort_values("type_strength", ascending=False)
        .drop_duplicates(subset=["artists"])
        .head(k)
        [["track_id", "track_name", "artists", "track_genre", "popularity"]]
        .reset_index(drop=True)
    )


def _smoke_test() -> None:
    """Classify two distinct playlists and check the codes differ."""
    from .config import PROCESSED_PARQUET_PATH

    df = pd.read_parquet(PROCESSED_PARQUET_PATH)
    df = attach_track_axes(df)

    samples = {
        "Rock party":   df[df["meta_genre"] == "Rock"].sample(25, random_state=1),
        "Late chill":   df[df["meta_genre"] == "Chill"].sample(25, random_state=2),
        "Hip-hop heat": df[df["meta_genre"] == "HipHop"].sample(25, random_state=3),
    }
    for tag, p in samples.items():
        r = classify(p)
        print(f"[{tag:<14s}] -> {r.code} ({r.name_en} / {r.name_zh})")
        print(f"    axes: {r.axes}")
        print(f"    desc: {r.description('en')}")

    print()
    print("[type distribution across full library]")
    print(df["mbti_type"].value_counts().to_string())


if __name__ == "__main__":
    _smoke_test()
