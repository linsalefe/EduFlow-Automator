from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from config import settings

logger = logging.getLogger("eduflow.video_editor")


def generate_mock_video(script_text: str, output_path: Path) -> Path:
    """
    MOCK: cria um arquivo .txt representando o vídeo gerado.
    Depois trocamos por MoviePy + Sora.
    """
    try:
        settings.ensure_directories()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = (
            "=== MOCK VIDEO ASSET ===\n"
            f"Generated at: {datetime.now().isoformat()}\n\n"
            "SCRIPT:\n"
            f"{script_text}\n"
        )
        output_path.write_text(payload, encoding="utf-8")

        logger.info("✅ Mock video gerado: %s", output_path)
        return output_path
    except Exception as exc:
        logger.exception("❌ Falha ao gerar mock video: %s", exc)
        raise
