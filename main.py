from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from config import settings
from database.repository import ContentRecord, ContentRepository, compute_content_hash
from src.generators.gemini_client import GeminiClient
from src.processors.image_editor import ImageEditor

logger = logging.getLogger("eduflow.main")


def generate_one_static_post(niche: str, platform: str = "instagram") -> Path:
    """
    Pipeline:
      1) Gemini -> idea topic
      2) Gemini -> caption (title + caption + hashtags)
      3) Pillow -> gerar imagem post
      4) SQLite -> salvar histórico (evitar duplicatas)
    """
    repo = ContentRepository()
    llm = GeminiClient()
    editor = ImageEditor()

    # 1) Ideia
    ideas = llm.generate_topic_ideas(niche=niche, count=1)
    idea = ideas[0]
    topic = idea.get("topic", "").strip() or "Tópico sem título"

    # 2) Legenda estruturada
    caption_obj = llm.write_post_caption(topic=topic)
    title = (caption_obj.get("title") or topic).strip()
    caption = (caption_obj.get("caption") or "").strip()
    hashtags = caption_obj.get("hashtags") or []

    if isinstance(hashtags, list) and hashtags:
        hashtags_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
        full_caption = f"{caption}\n\n{hashtags_str}".strip()
    else:
        full_caption = caption

    # Hash para evitar duplicatas
    content_hash = compute_content_hash(topic=topic, caption=full_caption)
    if repo.exists_by_hash(content_hash):
        raise RuntimeError("Conteúdo duplicado detectado (hash já existe no DB). Tente rodar novamente.")

    # 3) Gerar imagem
    raw_base = Path("assets/raw/base.jpg")
    if not raw_base.exists():
        raise FileNotFoundError("Arquivo base não encontrado: assets/raw/base.jpg")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path("assets/processed") / f"post_{ts}.jpg"

    editor.create_post(
        raw_image_path=raw_base,
        title=title,
        subtitle=idea.get("angle"),
        output_path=out_path,
        dark_mode=True,
    )

    # 4) Salvar DB
    metadata = {
        "idea": idea,
        "caption_obj": caption_obj,
        "render": {"output": str(out_path)},
    }

    record = ContentRecord(
        content_type="post",
        platform=platform,
        topic=topic,
        caption=full_caption,
        asset_path=str(out_path),
        content_hash=content_hash,
        status="rendered",
        metadata_json=repo.to_metadata_json(metadata),
    )
    repo.insert(record)

    logger.info("✅ Pipeline finalizada. Post pronto em: %s", out_path)
    return out_path


def main() -> None:
    settings.ensure_directories()

    # Exemplo: nicho inicial
    niche = "captação de matrículas para faculdades EAD"
    generate_one_static_post(niche=niche, platform="instagram")


if __name__ == "__main__":
    main()
