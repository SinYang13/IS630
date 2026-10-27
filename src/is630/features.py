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
