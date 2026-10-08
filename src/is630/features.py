"""Derived variables shared across stages. Defined once so the definitions
cannot drift between notebooks.

Columns are prefixed by source. `steam_` comes from the Steam dataset,
`hltb_` from HowLongToBeat. Columns built from both sources, or describing the
join itself, carry no prefix: `title_key`, `matched_hltb`, `year_diff` and
`completion_ratio`."""

import numpy as np
import pandas as pd

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
    """Count entries in a stringified list column such as supported languages."""
    cleaned = s.fillna("").astype(str).str.strip("[]")
    return cleaned.apply(lambda x: 0 if not x.strip() else len(x.split(",")))


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
