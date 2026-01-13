from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config.settings import DB_PATH

logger = logging.getLogger("eduflow.db")


@dataclass(frozen=True)
class ContentRecord:
    content_type: str   # "post" | "video"
    platform: str       # "instagram" | "tiktok"
    topic: str
    caption: str
    asset_path: str
    content_hash: str
    status: str = "created"
    metadata_json: Optional[str] = None


def compute_content_hash(topic: str, caption: str) -> str:
    payload = f"{topic.strip()}|{caption.strip()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ContentRepository:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def exists_by_hash(self, content_hash: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM content_history WHERE content_hash = ? LIMIT 1",
                (content_hash,),
            )
            return cur.fetchone() is not None

    def insert(self, record: ContentRecord) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO content_history
                (content_type, platform, topic, caption, asset_path, content_hash, status, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.content_type,
                    record.platform,
                    record.topic,
                    record.caption,
                    record.asset_path,
                    record.content_hash,
                    record.status,
                    record.metadata_json,
                ),
            )
            conn.commit()
            new_id = int(cur.lastrowid)
            logger.info("✅ Registro inserido no DB (id=%s)", new_id)
            return new_id

    def mark_status(self, content_hash: str, status: str) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE content_history SET status = ? WHERE content_hash = ?",
                (status, content_hash),
            )
            conn.commit()

    def mark_published(self, content_hash: str, platform_id: str, platform: str) -> None:
        """
        Marca como publicado e guarda o media_id (platform_id) no metadata_json.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT metadata_json FROM content_history WHERE content_hash = ? LIMIT 1",
                (content_hash,),
            )
            row = cur.fetchone()

            meta: dict[str, Any] = {}
            if row and row[0]:
                try:
                    meta = json.loads(row[0])
                    if not isinstance(meta, dict):
                        meta = {}
                except Exception:
                    meta = {}

            meta["published"] = {
                "platform": platform,
                "platform_id": platform_id,
                "published_at": datetime.now().isoformat(),
            }

            cur.execute(
                """
                UPDATE content_history
                SET status = ?, metadata_json = ?
                WHERE content_hash = ?
                """,
                ("published", json.dumps(meta, ensure_ascii=False), content_hash),
            )
            conn.commit()

    def to_metadata_json(self, data: dict[str, Any]) -> str:
        return json.dumps(data, ensure_ascii=False)
