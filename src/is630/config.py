"""Project paths, dataset pins and the random seed. Import from here, never hardcode."""

import hashlib
import zipfile
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
# continuously, so these must not change mid-project. The checksum is of the CSV
# inside the archive: Kaggle re-zips per download, so two downloads of the same
# version differ as zips but not in content.
STEAM_REF = "fronkongames/steam-games-dataset"
STEAM_VERSION = 49
STEAM_ZIP = RAW / f"steam_v{STEAM_VERSION}.zip"
STEAM_CSV = "games.csv"
STEAM_SHA256 = "1b48008b01a799d82385d6e66ba0cb65dd477b6aa4b6c2ec8c443025ab6880ad"
STEAM_RAW_ROWS = 125_855

HLTB_REF = "b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset"
HLTB_VERSION = 5
HLTB_ZIP = RAW / f"hltb_v{HLTB_VERSION}.zip"
HLTB_CSV = "hltb_dataset_normalized.csv"
HLTB_SHA256 = "59b91b918e685250a6d833634493de880028848fade00db41bdfee187cf5c56d"
HLTB_RAW_ROWS = 166_754

# Pinned row counts and sorted steam_appid SHA-256 fingerprints for the
# deduplicated join, the scope (story-driven and matched to HowLongToBeat), and the 80/20 train/test split
# drawn from that scope.
JOINED_ROWS = 121_284
JOINED_APPID_SHA256 = "0277513a92cee39bc7b706cfe6adaf97fabfdcc13ea38b8c000e0af9e524c8df"

SCOPED_ROWS = 6_601
SCOPED_APPID_SHA256 = "65303df87f57f12688a33b2caf17459c7387ef7a4075a1ac8e892a8f0230b7e4"

TRAIN_ROWS = 5_281
TRAIN_APPID_SHA256 = "4a98dafd48a34d0baa5d0d67e7f6f34cfc2541cb969fc220ed66a97c2f8271ea"

TEST_ROWS = 1_320
TEST_APPID_SHA256 = "9675b95cd06e63c3f005c98973c54d92057d2c08463e540d12dc71265f516ca1"

# Year the Steam archive was pulled. Used for game age, so it stays fixed with
# the pinned dataset rather than moving with the clock.
SNAPSHOT_YEAR = 2026


def verify_sha256(path: Path, member: str, expected_hex: str) -> str:
    """Compute the SHA-256 hex digest of one file inside a zip and assert it matches the pin."""
    h = hashlib.sha256()
    with zipfile.ZipFile(path) as z, z.open(member) as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if actual != expected_hex:
        raise ValueError(
            f"SHA-256 mismatch for {member} in {path.name}: expected {expected_hex}, got {actual}. "
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
