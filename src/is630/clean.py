"""Shared cleaning helpers. Keep the title normaliser and the column renamer
here so the join key and the column names cannot drift between stages."""

import re

import pandas as pd


def normalise_title(s: pd.Series) -> pd.Series:
    """Lowercase, strip trademark marks, reduce anything non-alphanumeric to a
    single space. Used to build the Steam to HowLongToBeat join key."""
    out = s.fillna("").astype(str).str.lower()
    # Not a raw string: Python turns the escapes into \u2122\u00ae\u00a9 itself, because the
    # pyarrow regex engine in newer pandas rejects \u escapes.
    out = out.str.replace("[\u2122\u00ae\u00a9]", "", regex=True)
    out = out.str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
    return out


def snake_case(name: str) -> str:
    """'Median playtime forever' -> 'median_playtime_forever'."""
    out = re.sub(r"[^0-9a-zA-Z]+", "_", str(name))
    return re.sub(r"_+", "_", out).strip("_").lower()


def prefix_columns(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Snake-case every column and stamp it with its source, so no column in the
    joined table is ambiguous about which dataset it came from.

    Both sources carry a name, a release date, a genre list and hour-valued
    columns, so the prefix is what keeps them apart downstream."""
    return df.rename(columns={c: f"{prefix}_{snake_case(c)}" for c in df.columns})
