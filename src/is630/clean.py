"""Shared cleaning helpers. Keep the title normaliser here so the join key cannot
drift between stages."""

import pandas as pd


def normalise_title(s: pd.Series) -> pd.Series:
    """Lowercase, strip trademark marks, reduce anything non-alphanumeric to a
    single space. Used to build the Steam to HowLongToBeat join key."""
    out = s.fillna("").astype(str).str.lower()
    out = out.str.replace(r"[\u2122\u00ae\u00a9]", "", regex=True)
    out = out.str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
    return out
