"""Project paths, dataset pins and the random seed. Import from here, never hardcode."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
EXTERNAL = DATA / "external"

OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"
MODELS = OUTPUTS / "models"

SEED = 42

# Pinned dataset versions and SHA-256 checksums. The Steam dataset refreshes
# continuously, so these must not change mid-project.
STEAM_REF = "fronkongames/steam-games-dataset"
STEAM_VERSION = 49
STEAM_ZIP = RAW / f"steam_v{STEAM_VERSION}.zip"
STEAM_SHA256 = "b0f431a6b2bec53b280a88efe64277b4df90ec2628a4d88d5efbdf25ad90786a"
STEAM_RAW_ROWS = 125_855

HLTB_REF = "b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset"
HLTB_VERSION = 5
HLTB_ZIP = RAW / f"hltb_v{HLTB_VERSION}.zip"
HLTB_SHA256 = "b155411befeea08b8228ea999850e19882c498fa1433247d72e86a2d29867648"
HLTB_RAW_ROWS = 166_754

# Pinned row counts and sorted steam_appid SHA-256 fingerprints for the
# deduplicated join and 80/20 train/test split.
JOINED_ROWS = 121_284
JOINED_APPID_SHA256 = "0277513a92cee39bc7b706cfe6adaf97fabfdcc13ea38b8c000e0af9e524c8df"

TRAIN_ROWS = 97_026
TRAIN_APPID_SHA256 = "4279b52ec340ab88560ebc3493d6b4ef9812a950da1441aa370ce90af2be379d"

TEST_ROWS = 24_258
TEST_APPID_SHA256 = "1f3b350373bfe4c4a1e6a30c97465ebb674dadff9723c8b87ef52039ff2cdb38"

# Year the Steam archive was pulled. Used for game age, so it stays fixed with
# the pinned dataset rather than moving with the clock.
SNAPSHOT_YEAR = 2026


def verify_sha256(path: Path, expected_hex: str) -> str:
    """Compute the SHA-256 hex digest of a file and assert it matches the pin."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if actual != expected_hex:
        raise ValueError(
            f"SHA-256 mismatch for {path.name}: expected {expected_hex}, got {actual}. "
            "Do not use an unpinned re-download; copy the pinned archive from the shared Drive."
        )
    return actual


def verify_appid_fingerprint(
    df: pd.DataFrame, expected_hex: str, label: str = "dataset"
) -> str:
    """Hash the sorted steam_appid column to verify the exact set of games matches the pin."""
    ids = np.sort(df["steam_appid"].to_numpy(dtype=np.int64))
    actual = hashlib.sha256(ids.tobytes()).hexdigest()
    if actual != expected_hex:
        raise ValueError(
            f"steam_appid fingerprint mismatch for {label}: expected {expected_hex}, got {actual}. "
            "Re-run Notebook 00 from the pinned raw archives."
        )
    return actual
