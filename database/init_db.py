from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Final

from config.settings import DB_PATH, ensure_directories

logger = logging.getLogger("eduflow.init_db")


SCHEMA: Final[str] = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS content_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_type TEXT NOT NULL,          -- "post" | "video"
    platform TEXT NOT NULL,              -- "instagram" | "tiktok"
    topic TEXT NOT NULL,
    caption TEXT,
    asset_path TEXT,
    content_hash TEXT NOT NULL UNIQUE,   -- evita duplicatas
    status TEXT NOT NULL DEFAULT 'created', -- created|rendered|published|failed
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_history_created_at
ON content_history(created_at);

CREATE INDEX IF NOT EXISTS idx_content_history_type_platform
ON content_history(content_type, platform);
"""


def init_db(db_path: Path) -> None:
    try:
        ensure_directories()

        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

        logger.info("✅ Banco inicializado com sucesso em: %s", db_path)

    except sqlite3.Error as exc:
        logger.exception("❌ Erro ao inicializar SQLite: %s", exc)
        raise
    except Exception as exc:
        logger.exception("❌ Erro inesperado ao inicializar DB: %s", exc)
        raise


if __name__ == "__main__":
    init_db(DB_PATH)
