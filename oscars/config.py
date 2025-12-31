from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # zakłada, że /oscars jest w root projektu
TRANSFORMED = ROOT / "analitics" / "transformed"
FIG_GENDER = TRANSFORMED / "figures_gender"
FIG_ACTING = TRANSFORMED / "figures_acting"
DB_DIR = TRANSFORMED / "db"
