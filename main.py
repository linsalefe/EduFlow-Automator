# main.py
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from config import settings
from config.logging_config import setup_logging
from database.repository import ContentRecord, ContentRepository, compute_content_hash
from src.exceptions import ContentDuplicateError, GeminiAPIError, EduFlowError
from src.generators.gemini_client import GeminiClient
from src.processors.image_editor import ImageEditor

logger = logging.getLogger("eduflow.main")


def generate_one_static_post(niche: str, platform: str = "instagram") -> Path:
    """
    Pipeline completo:
      1) Gemini -> ideia de tópico
      2) Gemini -> caption estruturada
      3) ImageEditor -> gerar post
      4) SQLite -> salvar histórico
    """
    logger.info("📝 Iniciando pipeline para nicho: %s", niche)
    
    repo = ContentRepository()
    llm = GeminiClient()
    editor = ImageEditor()

    try:
        # 1) Ideia
        logger.info("🤖 Gerando ideia de tópico...")
        ideas = llm.generate_topic_ideas(niche=niche, count=1)
        idea = ideas[0]
        topic = idea.get("topic", "").strip() or "Tópico sem título"
        logger.info("✅ Tópico gerado: %s", topic)

        # 2) Legenda estruturada
        logger.info("✍️ Escrevendo legenda...")
        caption_obj = llm.write_post_caption(topic=topic)
        title = (caption_obj.get("title") or topic).strip()
        caption = (caption_obj.get("caption") or "").strip()
        hashtags = caption_obj.get("hashtags") or []

        if isinstance(hashtags, list) and hashtags:
            hashtags_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
            full_caption = f"{caption}\n\n{hashtags_str}".strip()
        else:
            full_caption = caption

        # 3) Gerar imagem
        logger.info("🎨 Gerando arte do post...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = settings.PROCESSED_DIR / f"post_{ts}.jpg"

        editor.create_post(
            title=title,
            subtitle=idea.get("angle"),
            kicker=idea.get("hook", "Educação & Carreira"),
            background_query="university students studying laptop modern",
            auto_fetch_background=True,
            output_path=out_path,
            template="estacio_like",
            add_logo=True,
        )

        # 4) Salvar DB (lança ContentDuplicateError se duplicado)
        logger.info("💾 Salvando no banco de dados...")
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
            content_hash=compute_content_hash(topic=topic, caption=full_caption),
            status="rendered",
            metadata_json=repo.to_metadata_json(metadata),
        )
        repo.insert(record)

        logger.info("✅ Pipeline finalizada com sucesso!")
        logger.info("📁 Post salvo em: %s", out_path)
        return out_path
        
    except ContentDuplicateError as exc:
        logger.warning("⚠️ %s", exc)
        logger.info("💡 Tente rodar novamente para gerar conteúdo novo.")
        raise
    except Exception as exc:
        logger.exception("❌ Erro no pipeline: %s", exc)
        raise


def main() -> None:
    # Configura logging
    setup_logging(level="INFO")
    
    settings.ensure_directories()

    try:
        niche = "captação de matrículas para faculdades EAD"
        generate_one_static_post(niche=niche, platform="instagram")
    except ContentDuplicateError:
        logger.info("🔄 Execute novamente para gerar conteúdo diferente.")
    except EduFlowError as exc:
        logger.error("❌ Erro EduFlow: %s", exc)
    except Exception as exc:
        logger.exception("❌ Erro fatal inesperado: %s", exc)
        raise


if __name__ == "__main__":
    main()