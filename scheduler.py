# scheduler.py
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import schedule
import time

from config import settings
from database.repository import ContentRepository, ContentRecord, compute_content_hash
from src.generators.gemini_client import GeminiClient
from src.generators.pexels_client import PexelsClient
from src.processors.image_editor import ImageEditor
from src.processors.video_editor import generate_mock_video
from src.publishers.instagram_api import InstagramPublisher

logger = logging.getLogger("eduflow.scheduler")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _create_static_post(topic: str, auto_publish: bool = False) -> Path:
    settings.ensure_directories()

    repo = ContentRepository()
    gemini = GeminiClient()
    editor = ImageEditor()
    pexels = PexelsClient()

    # 1) Gerar ideia
    ideas = gemini.generate_topic_ideas(niche=topic, count=1)
    idea = ideas[0]
    topic_text = idea.get("topic", "").strip() or "Tópico sem título"

    # 2) Gerar legenda
    caption_obj = gemini.write_post_caption(topic=topic_text)
    title = (caption_obj.get("title") or topic_text).strip()
    caption = (caption_obj.get("caption") or "").strip()
    hashtags = caption_obj.get("hashtags") or []

    if isinstance(hashtags, list) and hashtags:
        hashtags_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
        full_caption = f"{caption}\n\n{hashtags_str}".strip()
    else:
        full_caption = caption

    # Hash para evitar duplicatas
    content_hash = compute_content_hash(topic=topic_text, caption=full_caption)
    if repo.exists_by_hash(content_hash):
        logger.warning("⚠️ Conteúdo duplicado (hash já existe). Pulando.")
        return Path("assets/processed/duplicated.jpg")

    # 3) Background Pexels
    bg_path = pexels.get_background_for_query("university students studying laptop modern")

    # 4) Gerar imagem
    out_path = settings.PROCESSED_DIR / f"post_{_timestamp()}.jpg"
    image_path = editor.create_post(
        title=title,
        subtitle=idea.get("hook", ""),
        kicker=idea.get("angle", "Educação & Carreira"),
        background_path=bg_path,
        output_path=out_path,
        template="estacio_like",
        add_logo=True,
    )

    # 5) Salvar no DB
    record = ContentRecord(
        content_type="post",
        platform="instagram",
        topic=topic_text,
        caption=full_caption,
        asset_path=str(image_path),
        content_hash=content_hash,
        status="rendered",
        metadata_json=repo.to_metadata_json({"idea": idea, "caption_obj": caption_obj}),
    )
    content_id = repo.insert(record)
    logger.info("✅ Post gerado e registrado: %s (id=%s)", image_path, content_id)

    # 6) Publicar (opcional)
    if auto_publish:
        publisher = InstagramPublisher()
        media_id = publisher.publish_photo(image_path=image_path, caption=full_caption)
        repo.mark_published(content_hash, platform_id=media_id, platform="instagram")
        logger.info("✅ Publicado no Instagram (media_id=%s)", media_id)

    return image_path


def _create_video_mock(topic: str) -> Path:
    settings.ensure_directories()

    repo = ContentRepository()
    gemini = GeminiClient()

    # 1) Gerar ideia
    ideas = gemini.generate_topic_ideas(niche=topic, count=1)
    idea = ideas[0]
    topic_text = idea.get("topic", "").strip() or "Tópico sem título"

    # 2) Gerar script
    script_obj = gemini.write_video_script(topic=topic_text, duration_sec=30)
    script_text = str(script_obj)

    # Hash
    content_hash = compute_content_hash(topic=topic_text, caption=script_text)
    if repo.exists_by_hash(content_hash):
        logger.warning("⚠️ Vídeo duplicado (hash já existe). Pulando.")
        return Path("assets/processed/duplicated.txt")

    # 3) Gerar mock
    out_path = settings.PROCESSED_DIR / f"video_{_timestamp()}.txt"
    video_path = generate_mock_video(script_text=script_text, output_path=out_path)

    # 4) Salvar no DB
    record = ContentRecord(
        content_type="video_mock",
        platform="tiktok",
        topic=topic_text,
        caption=script_text,
        asset_path=str(video_path),
        content_hash=content_hash,
        status="rendered",
        metadata_json=repo.to_metadata_json({"idea": idea, "script": script_obj}),
    )
    content_id = repo.insert(record)
    logger.info("✅ Vídeo mock gerado e registrado: %s (id=%s)", video_path, content_id)

    return video_path


def run_scheduler() -> None:
    logger.info("🗓️ Scheduler iniciado. Aguardando horários...")

    niche = "captação de matrículas para faculdades EAD"

    # Posts estáticos
    schedule.every().day.at("09:00").do(_create_static_post, topic=niche, auto_publish=False)
    schedule.every().day.at("12:00").do(_create_static_post, topic=niche, auto_publish=False)
    schedule.every().day.at("18:00").do(_create_static_post, topic=niche, auto_publish=False)

    # Vídeos mock
    schedule.every().day.at("10:30").do(_create_video_mock, topic=niche)
    schedule.every().day.at("15:30").do(_create_video_mock, topic=niche)
    schedule.every().day.at("20:30").do(_create_video_mock, topic=niche)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s"
    )
    run_scheduler()