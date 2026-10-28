"""Derived variables shared across stages. Defined once so the definitions
cannot drift between notebooks.

Columns are prefixed by source. `steam_` comes from the Steam dataset,
`hltb_` from HowLongToBeat. Columns built from both sources, or describing the
join itself, carry no prefix: `title_key`, `matched_hltb`, `year_diff` and
`completion_ratio`."""

import numpy as np
import pandas as pd
import ast
import re

from . import config

OWNER_BUCKET_SEP = " - "


def review_count(df: pd.DataFrame) -> pd.Series:
    """Positive plus negative reviews.

    Stored as `steam_review_count`, not `steam_reviews`: the Steam file already
    has a `Reviews` column holding press quotes, which prefixes to
    `steam_reviews`, and reusing that name would silently overwrite it."""
    return df["steam_positive"] + df["steam_negative"]


def positive_rate(df: pd.DataFrame) -> pd.Series:
    """Share of reviews that are positive. NaN where there are no reviews, since
    the rate is undefined rather than zero."""
    n = review_count(df)
    return np.where(n > 0, df["steam_positive"] / n, np.nan)


def completion_ratio(df: pd.DataFrame) -> pd.Series:
    """Median hours played on Steam divided by the typical main-story hours from
    HowLongToBeat.

    Steam records playtime in minutes and HowLongToBeat in hours, so the
    numerator is converted. NaN where either side is missing. This column spans
    both sources, so it carries no prefix."""
    hours = df["steam_median_playtime_forever"] / 60.0
    out = hours / df["hltb_main_story"]
    return out.replace([np.inf, -np.inf], np.nan)


def owner_bounds(s: pd.Series) -> pd.DataFrame:
    """Split the bucketed owner range into its lower and upper bounds. The
    bucket is interval-censored, so both bounds are kept rather than a midpoint
    standing in for a count."""
    parts = s.fillna("").astype(str).str.split(OWNER_BUCKET_SEP, n=1, expand=True)
    lower = pd.to_numeric(parts[0], errors="coerce")
    upper = pd.to_numeric(parts[1], errors="coerce") if parts.shape[1] > 1 else np.nan
    return pd.DataFrame(
        {"steam_owners_lower": lower, "steam_owners_upper": upper}, index=s.index
    )



def list_length(s: pd.Series) -> pd.Series:
    """Count entries in a stringified list column such as supported_languages."""

    def count_items(value):
        if isinstance(value, (list, tuple, set)):
            return len(value)

        if pd.isna(value):
            return 0

        text = str(value).strip()

        if not text or text.lower() in ("nan", "none", "[]"):
            return 0

        # Parse properly formatted stringified lists
        try:
            parsed = ast.literal_eval(text)

            if isinstance(parsed, (list, tuple, set)):
                return sum(bool(str(item).strip()) for item in parsed)

            if isinstance(parsed, str):
                return int(bool(parsed.strip()))

        except (ValueError, SyntaxError):
            pass

        # Fallback for malformed stringified lists
        quoted_items = re.findall(r"""['"]([^'"]+)['"]""", text)

        if quoted_items:
            return len(quoted_items)

        # Fallback for comma-separated values
        return sum(
            bool(item.strip(" []'\""))
            for item in text.split(",")
        )

    return s.apply(count_items).astype(int)


def classify_story_driven(df: pd.DataFrame) -> pd.Series:
    """Identify single-player games with narrative tags or Visual Novel genre."""

    story_tags = [
        "Story Rich",
        "Visual Novel",
        "Interactive Fiction",
        "Narrative",
        "Choices Matter",
        "Choose Your Own Adventure"
    ]

    # Normalize relevant metadata
    categories = df["steam_categories"].fillna("").astype(str)
    tags = df["steam_tags"].fillna("").astype(str)
    genres = df["steam_genres"].fillna("").astype(str)

    # Identify single-player games
    single_player = categories.str.contains(
        "Single-player",
        case=False,
        regex=False
    )

    # Match complete narrative tag names
    tag_pattern = (
        r"(?<![A-Za-z0-9])(?:"
        + "|".join(re.escape(tag) for tag in story_tags)
        + r")(?![A-Za-z0-9])"
    )

    narrative_tags = tags.str.contains(
        tag_pattern,
        case=False,
        regex=True
    )

    # Check Visual Novel genre
    visual_novel_genre = genres.str.contains(
        r"(?<![A-Za-z0-9])Visual Novel(?![A-Za-z0-9])",
        case=False,
        regex=True
    )

    # Return final classification
    return (
        single_player
        & (narrative_tags | visual_novel_genre)
    ).rename("flag_story_driven")


def extract_primary_developer(
    dev_series: pd.Series,
    appid_series: pd.Series
) -> pd.Series:
    """Extract primary developer names for model grouping."""

    def get_primary_developer(value, appid):
        # Handle native lists
        if isinstance(value, (list, tuple)):
            developers = [
                str(x).strip()
                for x in value
                if str(x).strip()
            ]

            if developers:
                return developers[0].casefold()

        elif pd.notna(value):
            raw = str(value).strip()

            if raw and raw not in ("[]", "None", "nan"):
                try:
                    parsed = ast.literal_eval(raw)

                    if isinstance(parsed, (list, tuple)) and parsed:
                        return str(parsed[0]).strip().casefold()

                    if isinstance(parsed, str) and parsed.strip():
                        return parsed.strip().casefold()

                except (ValueError, SyntaxError):
                    pass

                # Fallback for non-standard strings
                fallback = (
                    raw.strip("[]")
                    .split(",")[0]
                    .strip(" '\"")
                )

                if fallback:
                    return fallback.casefold()

        # Unique group when developer information is missing
        return f"unknown_app_{appid}"

    if len(dev_series) != len(appid_series):
        raise ValueError(
            "Developer and App ID Series must have equal lengths."
        )

    return pd.Series(
        [
            get_primary_developer(developer, appid)
            for developer, appid in zip(dev_series, appid_series)
        ],
        index=dev_series.index,
        name="developer_group"
    )



def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Attach the derived columns every later stage expects."""
    out = df.copy()
    out["steam_review_count"] = review_count(out)
    out["steam_positive_rate"] = positive_rate(out)
    out["steam_playtime_hours"] = out["steam_median_playtime_forever"] / 60.0
    out["steam_years_since_release"] = config.SNAPSHOT_YEAR - out["steam_year"]
    out["steam_language_count"] = list_length(out["steam_supported_languages"])
    out["steam_has_metacritic"] = out["steam_metacritic_score"] > 0
    out["completion_ratio"] = completion_ratio(out)
    out = out.join(owner_bounds(out["steam_estimated_owners"]))
    return out


# Notebook 02's cleaning and feature steps, one function per step, so notebook
# 07 can put the test holdout through exactly the same code. Each returns a copy.

NON_GAME_GENRES = {
    "Utilities", "Design & Illustration", "Animation & Modeling", "Audio Production",
    "Video Production", "Photo Editing", "Software Training", "Web Publishing",
    "Game Development", "Accounting",
}
GENRE_MAP = {
    "Indie": "genre_indie", "Casual": "genre_casual", "Action": "genre_action",
    "Adventure": "genre_adventure", "Simulation": "genre_simulation",
    "Strategy": "genre_strategy", "RPG": "genre_rpg", "Early Access": "genre_early_access",
}
PRICE_BINS = [-0.01, 0, 5, 10, 20, np.inf]
PRICE_LABELS = ["Free", "0-5", "5-10", "10-20", "20+"]
CATEGORY_FLAGS = {
    "cat_singleplayer": ["Single-player"],
    "cat_multiplayer": ["Multi-player"],
    "cat_coop": ["Co-op", "Online Co-op", "LAN Co-op", "Shared/Split Screen Co-op"],
    "cat_controller": ["Full controller support", "Partial Controller Support", "Controller Support"],
    "cat_steam_cloud": ["Steam Cloud"],
    "cat_trading_cards": ["Steam Trading Cards"],
    "cat_vr": ["VR Supported", "VR Only", "VR Support"],
}
STORY_TAGS = ["Story Rich", "Visual Novel", "Interactive Fiction", "Narrative",
              "Choices Matter", "Choose Your Own Adventure"]


def is_software(genres: pd.Series) -> pd.Series:
    """True where a game carries a non-game genre such as Utilities (notebook 01)."""
    genre_sets = genres.fillna("").apply(lambda x: {t.strip() for t in x.split(",")})
    return genre_sets.apply(lambda s: bool(NON_GAME_GENRES & s))


def valid_rows(df: pd.DataFrame) -> pd.Series:
    """Rows kept by notebook 02: not software, review counts present and non-negative, price non-negative."""
    positive = pd.to_numeric(df["steam_positive"], errors="coerce")
    negative = pd.to_numeric(df["steam_negative"], errors="coerce")
    price = pd.to_numeric(df["steam_price"], errors="coerce")
    invalid_reviews = positive.isna() | negative.isna() | positive.lt(0) | negative.lt(0)
    return ~(df["steam_is_software"].fillna(False) | invalid_reviews | price.lt(0))


def add_cleaning_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["flag_zero_reviews"] = out["steam_review_count"] == 0
    out["flag_free_to_play"] = out["steam_price"] == 0
    hours = pd.to_numeric(out["steam_playtime_hours"], errors="coerce")
    out["flag_extreme_playtime"] = hours.lt(0) | hours.gt(8760)
    # Only positive, non-extreme playtime feeds the completion ratio
    out["steam_playtime_hours_usable"] = hours.where(hours.gt(0) & hours.le(8760))
    return out


def add_story_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    categories = out["steam_categories"].fillna("").astype(str)
    tags = out["steam_tags"].fillna("").astype(str)
    genres = out["steam_genres"].fillna("").astype(str)
    out["flag_single_player"] = categories.str.contains("Single-player", case=False, regex=False)
    # Whole tag names only, not arbitrary substrings
    tag_pattern = r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(t) for t in STORY_TAGS) + r")(?![A-Za-z0-9])"
    out["flag_narrative_tags"] = tags.str.contains(tag_pattern, case=False, regex=True)
    out["flag_visual_novel_genre"] = genres.str.contains(r"(?<![A-Za-z0-9])Visual Novel(?![A-Za-z0-9])", case=False, regex=True)
    out["flag_story_driven"] = classify_story_driven(out)
    out["flag_missing_story_metadata"] = out["steam_categories"].isna() | out["steam_tags"].isna()
    return out


def add_target_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    main_story = pd.to_numeric(out["hltb_main_story"], errors="coerce")
    completion_eligible = (out["flag_story_driven"] & out["matched_hltb"].fillna(False)
                           & main_story.gt(0) & out["steam_playtime_hours_usable"].gt(0))
    out["flag_reception_eligible"] = out["steam_review_count"] > 0
    out["flag_completion_eligible"] = completion_eligible & out["completion_ratio"].gt(0)
    return out


def _has_value(series: pd.Series) -> pd.Series:
    values = series.fillna("").astype(str).str.strip().str.casefold()
    return ~values.isin(["", "none", "nan"])


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Genres, price, release quarter, platforms, audio, achievements, age rating,
    store categories, tags, publishing, storefront and HLTB scope features."""
    out = df.copy()
    genre_sets = out["steam_genres"].fillna("").apply(lambda x: {g.strip() for g in x.split(",")})
    for genre, column in GENRE_MAP.items():
        out[column] = genre_sets.apply(lambda genres: int(genre in genres))
    out["flag_missing_genre"] = out["steam_genres"].isna().astype(int)

    out["feature_log_price"] = np.log1p(out["steam_price"])
    out["feature_price_band"] = pd.cut(out["steam_price"], bins=PRICE_BINS, labels=PRICE_LABELS, include_lowest=True)
    dummies = pd.get_dummies(out["feature_price_band"], prefix="price_band", dtype=int)
    out = pd.concat([out.loc[:, ~out.columns.str.startswith("price_band_")], dummies], axis=1)

    release = pd.to_datetime(out["steam_release_date"], errors="coerce", format="mixed")
    out["flag_q4_release"] = release.dt.month.isin([10, 11, 12]).astype(int)
    out["steam_mac"] = out["steam_mac"].astype(int)
    out["steam_linux"] = out["steam_linux"].astype(int)

    out["steam_audio_language_count"] = list_length(out["steam_full_audio_languages"])
    out["feature_log_audio_language_count"] = np.log1p(out["steam_audio_language_count"])
    out["flag_has_full_audio"] = (out["steam_audio_language_count"] > 0).astype(int)

    assert out["steam_achievements"].ge(0).all()
    out["feature_log_achievements"] = np.log1p(out["steam_achievements"])
    out["flag_has_achievements"] = (out["steam_achievements"] > 0).astype(int)
    out["flag_age_restricted"] = pd.to_numeric(out["steam_required_age"], errors="coerce").fillna(0).gt(0).astype(int)

    category_sets = out["steam_categories"].fillna("").apply(
        lambda value: {item.strip().casefold() for item in str(value).split(",") if item.strip()})
    for flag, names in CATEGORY_FLAGS.items():
        wanted = {n.casefold() for n in names}
        out[flag] = category_sets.apply(lambda values: int(bool(values & wanted)))

    out["flag_missing_tags"] = (out["steam_tags"].fillna("").astype(str).str.strip().str.lower()
                                .isin(["", "[]", "none", "nan"]).astype(int))
    developers = out["steam_developers"].fillna("").astype(str).str.strip().str.casefold()
    publishers = out["steam_publishers"].fillna("").astype(str).str.strip().str.casefold()
    out["flag_self_published"] = (developers.ne("") & publishers.ne("") & developers.eq(publishers)).astype(int)
    out["flag_has_website"] = _has_value(out["steam_website"]).astype(int)
    out["flag_has_support_contact"] = (_has_value(out["steam_support_url"]) | _has_value(out["steam_support_email"])).astype(int)

    out["feature_log_main_story_hours"] = np.log1p(out["hltb_main_story"])
    out["flag_has_side_content"] = (out["hltb_main_plus_sides"] > out["hltb_main_story"]).astype(int)
    return out


def _language_count_strict(value):
    """Unique entries of a well-formed list string, else NaN."""
    if pd.isna(value) or not str(value).strip():
        return np.nan
    try:
        languages = ast.literal_eval(str(value))
    except (ValueError, SyntaxError):
        return np.nan
    if not isinstance(languages, (list, tuple)) or not languages:
        return np.nan
    return len(set(str(x).strip() for x in languages))


def parse_supported_languages(value):
    """(unique language count, parse status). Falls back to splitting on quotes
    for list strings that literal_eval rejects, such as names containing an apostrophe."""
    if pd.isna(value) or not str(value).strip():
        return np.nan, "missing"
    text = str(value).strip()
    try:
        languages = ast.literal_eval(text)
        if isinstance(languages, (list, tuple)):
            return len({str(x).strip() for x in languages if str(x).strip()}), "standard"
    except (ValueError, SyntaxError):
        pass
    if not (text.startswith("[") and text.endswith("]")):
        return np.nan, "unparseable"
    inner = text[1:-1].strip()
    if not inner:
        return 0, "empty"
    quote = inner[0]
    if quote not in ("'", '"') or not inner.endswith(quote):
        return np.nan, "unparseable"
    parts = [p.strip() for p in re.split(re.escape(quote) + r"\s*,\s*" + re.escape(quote), inner[1:-1])]
    if not all(parts):
        return np.nan, "unparseable"
    return len(set(parts)), "fallback"


def add_language_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["feature_language_count_parsed"] = out["steam_supported_languages"].apply(_language_count_strict)
    parsed = out["steam_supported_languages"].apply(parse_supported_languages)
    out[["feature_language_count", "language_parse_status"]] = pd.DataFrame(parsed.tolist(), index=out.index)
    out["flag_missing_language_metadata"] = out["feature_language_count"].isna()
    out["language_count_difference"] = out["steam_language_count"] - out["feature_language_count"]
    # Zero recorded languages means the information is missing, not that no language is supported
    out["flag_zero_languages"] = out["feature_language_count"] == 0
    out["feature_language_count_model"] = out["feature_language_count"].mask(out["flag_zero_languages"])
    out["feature_log_language_count"] = np.log1p(out["feature_language_count_model"])
    return out


def add_eligibility_flags(df: pd.DataFrame, min_reviews_reception: int, min_reviews_completion: int,
                          min_hltb_polls: int) -> pd.DataFrame:
    """Model inclusion flags. The thresholds are set in notebook 02 and saved in its feature spec."""
    out = df.copy()
    polls = pd.to_numeric(out["hltb_main_story_polled"], errors="coerce")
    out["flag_reception_model"] = out["steam_review_count"] >= min_reviews_reception
    out["flag_completion_model"] = (out["flag_completion_eligible"]
                                    & (out["steam_review_count"] >= min_reviews_completion)
                                    & (polls >= min_hltb_polls))
    return out


def build_features(df: pd.DataFrame, min_reviews_reception: int, min_reviews_completion: int,
                   min_hltb_polls: int) -> pd.DataFrame:
    """Every per-row step of notebooks 01 and 02, in order, from a 00-stage table.
    Drops the rows notebook 02 excludes. Training statistics are applied separately."""
    out = add_derived(df)
    out["steam_is_software"] = is_software(out["steam_genres"])
    out = out.loc[valid_rows(out)].copy()
    for step in (add_cleaning_flags, add_story_flags, add_target_flags, encode_features, add_language_features):
        out = step(out)
    return add_eligibility_flags(out, min_reviews_reception, min_reviews_completion, min_hltb_polls)


def apply_training_stats(df: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    """The two steps that use training data: each developer's game count and the
    median language count used for imputation. `train` must have been through
    build_features. Works for the training set itself and for any later set."""
    out = df.copy()
    out["developer_group"] = extract_primary_developer(out["steam_developers"], out["steam_appid"])
    counts = extract_primary_developer(train["steam_developers"], train["steam_appid"]).value_counts()
    # Count a developer's OTHER training games, so a training game does not count itself
    in_train = out["steam_appid"].isin(train["steam_appid"]).astype(int)
    out["feature_log_dev_game_count"] = np.log1p(out["developer_group"].map(counts).fillna(0) - in_train)
    median = train["feature_language_count_model"].median()
    out["feature_language_missing"] = out["feature_language_count_model"].isna().astype(int)
    out["feature_language_count_imputed"] = out["feature_language_count_model"].fillna(median)
    out["feature_log_language_count_imputed"] = np.log1p(out["feature_language_count_imputed"])
    return out
