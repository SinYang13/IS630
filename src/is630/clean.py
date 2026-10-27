"""Shared cleaning helpers. Keep the title normaliser and the column renamer
here so the join key and the column names cannot drift between stages."""

import re
import unicodedata

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


# Edition and re-release suffixes that Steam appends to a store name but
# HowLongToBeat folds into the base game. Matched only at the end of the key.
EDITION_SUFFIX = (
    r"\b(game of the year|goty|definitive|complete|enhanced|ultimate|deluxe|gold|premium"
    r"|anniversary|special|collector s|legendary|royal|digital|standard|director s cut"
    r"|reloaded|remastered|hd|classic)\b( edition)?$"
)


def loose_title(s: pd.Series) -> pd.Series:
    """Fallback join key for titles the exact key leaves unmatched.

    On top of `normalise_title` it drops accents, reads '&' as 'and', and strips
    a trailing '(2005)' and edition suffixes such as 'GOTY Edition' or
    "Director's Cut". A leading 'the' and a bare trailing year are kept on
    purpose: stripping them merged different games, for example 'Football
    Manager 2020' with 'Football Manager 2022'."""
    out = s.fillna("").astype(str).map(
        lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode()
    )
    out = out.str.replace("&", " and ", regex=False)
    out = out.str.replace(r"\s*\((19|20)\d\d\)\s*$", "", regex=True)
    out = normalise_title(out)
    out = out.str.replace(r"\b(19|20)\d\d edition$", "", regex=True).str.strip()
    # Twice, so stacked suffixes like 'enhanced edition director s cut' both go
    for _ in range(2):
        out = out.str.replace(r"\b(edition|version)$", "", regex=True).str.strip()
        out = out.str.replace(EDITION_SUFFIX, "", regex=True).str.strip()
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
