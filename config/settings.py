# config/settings.py
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# Paths (raiz do projeto)
# -----------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

ASSETS_DIR: Path = PROJECT_ROOT / "assets"
RAW_DIR: Path = ASSETS_DIR / "raw"
PROCESSED_DIR: Path = ASSETS_DIR / "processed"
TEMP_DIR: Path = ASSETS_DIR / "temp"

BACKGROUNDS_DIR: Path = RAW_DIR / "backgrounds"
FONTS_DIR: Path = RAW_DIR / "fonts"
LOGOS_DIR: Path = RAW_DIR / "logos"

# DB
DB_DIR: Path = PROJECT_ROOT / "database"
DB_PATH: Path = DB_DIR / "content_history.db"


# -----------------------------
# Brand (EduFlow IA)
# -----------------------------
COLOR_PRIMARY = "#6366f1"
COLOR_DARK = "#0f172a"
COLOR_ACCENT = "#818cf8"
COLOR_WHITE = "#ffffff"
COLOR_TEXT = "#334155"
COLOR_BG_LIGHT = "#f1f5f9"

# Gradiente principal (hero)
GRADIENT_A = "#1e1b4b"
GRADIENT_B = "#4338ca"

# Post (Instagram feed)
POST_WIDTH = 1080
POST_HEIGHT = 1350
POST_SIZE = (POST_WIDTH, POST_HEIGHT)
SAFE_MARGIN = 72


# -----------------------------
# Logo (prioriza sem fundo)
# -----------------------------
def _resolve_first_existing(paths: list[Path]) -> Path:
    for p in paths:
        if p.exists():
            return p
    return paths[0] if paths else PROJECT_ROOT / "logo.png"


LOGO_PATH: Path = _resolve_first_existing(
    [
        RAW_DIR / "logo_sem_fundo.png",
        RAW_DIR / "lodo_sem_fundo.png",
        RAW_DIR / "logo.png",
        LOGOS_DIR / "logo_sem_fundo.png",
        LOGOS_DIR / "lodo_sem_fundo.png",
        LOGOS_DIR / "logo.png",
    ]
)


# -----------------------------
# Fonts (Inter)
# -----------------------------
def _find_font_file() -> dict[str, Path]:
    candidates = [
        ("regular", FONTS_DIR / "Inter" / "static" / "Inter-Regular.ttf"),
        ("medium", FONTS_DIR / "Inter" / "static" / "Inter-Medium.ttf"),
        ("semibold", FONTS_DIR / "Inter" / "static" / "Inter-SemiBold.ttf"),
        ("extrabold", FONTS_DIR / "Inter" / "static" / "Inter-ExtraBold.ttf"),
        ("regular", FONTS_DIR / "static" / "Inter-Regular.ttf"),
        ("medium", FONTS_DIR / "static" / "Inter-Medium.ttf"),
        ("semibold", FONTS_DIR / "static" / "Inter-SemiBold.ttf"),
        ("extrabold", FONTS_DIR / "static" / "Inter-ExtraBold.ttf"),
    ]

    resolved: dict[str, Path] = {}
    for key, path in candidates:
        if key not in resolved and path.exists():
            resolved[key] = path

    variable = [
        FONTS_DIR / "Inter" / "Inter-VariableFont_opsz,wght.ttf",
        FONTS_DIR / "Inter-VariableFont_opsz,wght.ttf",
        FONTS_DIR / "Inter" / "Inter-VariableFont_slnt,wght.ttf",
        FONTS_DIR / "Inter-VariableFont_slnt,wght.ttf",
    ]
    var_path = next((p for p in variable if p.exists()), None)

    if var_path:
        resolved.setdefault("regular", var_path)
        resolved.setdefault("medium", var_path)
        resolved.setdefault("semibold", var_path)
        resolved.setdefault("extrabold", var_path)

    resolved.setdefault("regular", FONTS_DIR / "Inter-Regular.ttf")
    resolved.setdefault("medium", FONTS_DIR / "Inter-Medium.ttf")
    resolved.setdefault("semibold", FONTS_DIR / "Inter-SemiBold.ttf")
    resolved.setdefault("extrabold", FONTS_DIR / "Inter-ExtraBold.ttf")
    return resolved


_FONT = _find_font_file()
FONT_REGULAR: Path = _FONT["regular"]
FONT_MEDIUM: Path = _FONT["medium"]
FONT_SEMIBOLD: Path = _FONT["semibold"]
FONT_EXTRABOLD: Path = _FONT["extrabold"]


# -----------------------------
# APIs / ENV
# -----------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

INSTAGRAM_USER: str = os.getenv("INSTAGRAM_USER", "")
INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")

# Pexels
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")

IG_SESSION_PATH: Path = TEMP_DIR / "instagram_session.json"


# -----------------------------
# Helpers
# -----------------------------
def ensure_directories() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)

    DB_DIR.mkdir(parents=True, exist_ok=True)
