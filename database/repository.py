# database/repository.py
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
from src.exceptions import ContentDuplicateError, EduFlowError

logger = logging.getLogger("eduflow.db")


@dataclass(frozen=True)
class ContentRecord:
    content_type: str   # "post" | "video" | "carousel"
    platform: str       # "instagram" | "tiktok"
    topic: str
    caption: str
    asset_path: str
    content_hash: str
    status: str = "created"
    metadata_json: Optional[str] = None


def compute_content_hash(topic: str, caption: str) -> str:
    """Gera hash SHA256 do conteúdo para detectar duplicatas"""
    payload = f"{topic.strip()}|{caption.strip()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ContentRepository:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as exc:
            raise EduFlowError(f"Erro ao conectar no banco: {exc}") from exc

    def exists_by_hash(self, content_hash: str) -> bool:
        """Verifica se já existe conteúdo com este hash"""
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT 1 FROM content_history WHERE content_hash = ? LIMIT 1",
                    (content_hash,),
                )
                return cur.fetchone() is not None
        except sqlite3.Error as exc:
            logger.exception("Erro ao verificar hash: %s", exc)
            return False

    def insert(self, record: ContentRecord) -> int:
        """
        Insere novo registro no banco.
        Raises ContentDuplicateError se hash já existe.
        """
        if self.exists_by_hash(record.content_hash):
            raise ContentDuplicateError(
                f"Conteúdo duplicado detectado (hash={record.content_hash[:12]}...)"
            )
        
        try:
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
                logger.info("✅ Registro inserido no DB (id=%s, hash=%s...)", new_id, record.content_hash[:12])
                return new_id
        except sqlite3.IntegrityError as exc:
            raise ContentDuplicateError(f"Violação de integridade: {exc}") from exc
        except sqlite3.Error as exc:
            raise EduFlowError(f"Erro ao inserir no banco: {exc}") from exc

    def mark_status(self, content_hash: str, status: str) -> None:
        """Atualiza status do conteúdo"""
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE content_history SET status = ? WHERE content_hash = ?",
                    (status, content_hash),
                )
                conn.commit()
                logger.info("✅ Status atualizado para '%s' (hash=%s...)", status, content_hash[:12])
        except sqlite3.Error as exc:
            logger.exception("Erro ao atualizar status: %s", exc)

    def mark_published(self, content_hash: str, platform_id: str, platform: str) -> None:
        """Marca como publicado e guarda metadata de publicação"""
        try:
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
                    except json.JSONDecodeError:
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
                logger.info("✅ Marcado como publicado (hash=%s..., platform_id=%s)", content_hash[:12], platform_id)
        except sqlite3.Error as exc:
            logger.exception("Erro ao marcar como publicado: %s", exc)

    def to_metadata_json(self, data: dict[str, Any]) -> str:
        """Converte dict para JSON string"""
        return json.dumps(data, ensure_ascii=False)
    