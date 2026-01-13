from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import schedule
import time

from config import settings
from database.db import insert_content_record
from src.generators.gemini_client import GeminiClient
from src.generators.stock_images import PexelsImageBank
from src.processors.image_editor import ImageEditor
from src.processors.video_editor import create_short_video_mock
from src.publishers.instagram_api import InstagramPublisher

logger = logging.getLogger("eduflow.scheduler")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _best_pexels_query(topic: str) -> str:
    """
    Query mais "fotografável" para banco de imagens.
    """
    # simplifica termos muito específicos
    base = topic.lower()
    if "ead" in base or "ensino a distância" in base:
        return "student studying with laptop online learning"
    if "matrícula" in base or "captação" in base:
        return "college student laptop enrollment education"
    return "education student laptop modern"


def _get_background_image(topic: str) -> str:
    """
    Retorna um caminho de imagem local.
    Usa Pexels se tiver chave; caso contrário, tenta assets/raw/base.jpg.
    """
    fallback = Path(settings.RAW_DIR) / "base.jpg"
    if settings.PEXELS_API_KEY:
        pexels = PexelsImageBank(api_key=settings.PEXELS_API_KEY)
        query = _best_pexels_query(topic)
        return pexels.download_first(query=query, out_dir=str(Path(settings.RAW_DIR) / "stock"))
    if fallback.exists():
        return fallback.as_posix()
    # último fallback: gera fundo sólido (ImageEditor lida)
    return fallback.as_posix()


def _create_static_post(topic: str, auto_publish: bool = False) -> str:
    settings.ensure_directories()

    gemini = GeminiClient()
    editor = ImageEditor()

    bg_path = _get_background_image(topic)

    ideas = gemini.generate_topic_ideas(topic, count=1)
    idea = ideas[0]

    # legenda
    caption = gemini.write_post_caption(
        topic=idea["topic"],
        angle=idea.get("angle", ""),
        hook=idea.get("hook", ""),
        target=idea.get("target", ""),
    )

    # arte single (bem “institucional”)
    title = idea["topic"]
    subtitle = idea.get("hook", "")
    kicker = "Educação & Carreira"

    out = Path(settings.PROCESSED_DIR) / f"post_{_timestamp()}.jpg"
    image_path = editor.create_post(
        image_path=bg_path,
        title=title,
        subtitle=subtitle,
        kicker=kicker,
        template="educational",
        output_path=out.as_posix(),
        logo_path=str(settings.LOGO_PATH),
    )

    content_id = insert_content_record(
        content_type="post",
        topic=idea["topic"],
        caption=caption,
        asset_path=image_path,
    )
    logger.info("✅ Post gerado e registrado: %s (id=%s)", image_path, content_id)

    if auto_publish:
        publisher = InstagramPublisher()
        media_id = publisher.publish_photo(image_path=image_path, caption=caption)
        logger.info("✅ Publicado no Instagram (media_id=%s)", media_id)

    return image_path


def _create_carousel_post(topic: str, auto_publish: bool = False) -> List[str]:
    settings.ensure_directories()

    gemini = GeminiClient()
    editor = ImageEditor()

    bg_path = _get_background_image(topic)

    ideas = gemini.generate_topic_ideas(topic, count=1)
    idea = ideas[0]

    # roteiro curtinho para virar carrossel (3 páginas)
    # (Simples e eficiente: capa + 3 bullets + CTA)
    title = idea["topic"]
    hook = idea.get("hook", "Aprenda de forma prática e sem enrolação.")
    angle = idea.get("angle", "Guia rápido")

    bullets = gemini.generate_bullets(topic=title, count=4)

    slides: List[Dict] = [
        {
            "template": "promo",
            "kicker": angle,
            "title": "EAD Sem Segredos",
            "subtitle": hook,
            "cta": "SALVE ESTE POST",
        },
        {
            "template": "educational",
            "kicker": "Pontos-chave",
            "title": "O que ninguém te conta:",
            "bullets": bullets,
        },
        {
            "template": "promo",
            "kicker": "Próximo passo",
            "title": "Quer ajuda pra escolher o curso?",
            "subtitle": "Comenta “EAD” ou chama no direct.",
            "cta": "LINK NA BIO",
        },
    ]

    base = f"carousel_{_timestamp()}"
    paths = editor.create_carousel(
        image_path=bg_path,
        slides=slides,
        output_dir=str(settings.PROCESSED_DIR),
        basename=base,
        template_default="educational",
        logo_path=str(settings.LOGO_PATH),
    )

    # legenda mais curta para carrossel
    caption = gemini.write_carousel_caption(
        topic=title,
        hook=hook,
        bullets=bullets,
    )

    # registra no DB (uma entrada por carrossel, guardando a capa como asset principal)
    content_id = insert_content_record(
        content_type="carousel",
        topic=title,
        caption=caption,
        asset_path=paths[0],
    )
    logger.info("✅ Carrossel gerado e registrado: %s (id=%s)", paths[0], content_id)

    # (upload de carrossel no Instagram é outro método — se você quiser eu implemento já já)
    if auto_publish:
        publisher = InstagramPublisher()
        publisher.publish_carousel(image_paths=paths, caption=caption)
        logger.info("✅ Carrossel publicado no Instagram.")

    return paths


def _create_short_video_mock_task(topic: str, auto_publish: bool = False) -> str:
    settings.ensure_directories()

    gemini = GeminiClient()

    ideas = gemini.generate_topic_ideas(topic, count=1)
    idea = ideas[0]

    script = gemini.write_video_script(topic=idea["topic"], angle=idea.get("angle", ""), hook=idea.get("hook", ""))
    out = Path(settings.PROCESSED_DIR) / f"video_{_timestamp()}.txt"

    video_path = create_short_video_mock(script=script, output_path=out.as_posix())

    content_id = insert_content_record(
        content_type="video_mock",
        topic=idea["topic"],
        caption=script,
        asset_path=video_path,
    )
    logger.info("✅ Vídeo (mock) gerado e registrado: %s (id=%s)", video_path, content_id)

    return video_path


def run_scheduler() -> None:
    logger.info("🗓️ Scheduler iniciado. Aguardando horários...")

    # Exemplo (ajuste horários depois):
    schedule.every().day.at("09:00").do(_create_carousel_post, topic="captação de matrículas para faculdades EAD", auto_publish=False)
    schedule.every().day.at("12:00").do(_create_static_post, topic="captação de matrículas para faculdades EAD", auto_publish=False)
    schedule.every().day.at("18:00").do(_create_static_post, topic="captação de matrículas para faculdades EAD", auto_publish=False)

    # 3 vídeos mock
    schedule.every().day.at("10:30").do(_create_short_video_mock_task, topic="captação de matrículas para faculdades EAD")
    schedule.every().day.at("15:30").do(_create_short_video_mock_task, topic="captação de matrículas para faculdades EAD")
    schedule.every().day.at("20:30").do(_create_short_video_mock_task, topic="captação de matrículas para faculdades EAD")

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s")
    run_scheduler()
