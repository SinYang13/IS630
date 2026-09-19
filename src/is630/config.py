"""Project paths, dataset pins and the random seed. Import from here, never hardcode."""

from pathlib import Path

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

# Pinned dataset versions. The Steam dataset refreshes continuously, so these
# must not change mid-project.
STEAM_REF = "fronkongames/steam-games-dataset"
STEAM_VERSION = 49
STEAM_ZIP = RAW / f"steam_v{STEAM_VERSION}.zip"

HLTB_REF = "b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset"
HLTB_VERSION = 5
HLTB_ZIP = RAW / f"hltb_v{HLTB_VERSION}.zip"
