# main_html.py
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from config import settings
from config.logging_config import setup_logging
from database.repository import ContentRecord, ContentRepository, compute_content_hash
from src.exceptions import ContentDuplicateError
from src.generators.gemini_client import GeminiClient
from src.generators.pexels_client import PexelsClient
from src.processors.html_renderer import HtmlRenderer

logger = logging.getLogger("eduflow.main_html")


async def generate_one_html_post(niche: str, platform: str = "instagram") -> Path:
    """
    Pipeline HTML/CSS para posts profissionais.
    """
    logger.info("📝 Iniciando pipeline HTML para nicho: %s", niche)
    
    repo = ContentRepository()
    llm = GeminiClient()
    pexels = PexelsClient()
    renderer = HtmlRenderer()

    try:
        # 1) Gerar ideia
        logger.info("🤖 Gerando ideia de tópico...")
        ideas = llm.generate_topic_ideas(niche=niche, count=1)
        idea = ideas[0]
        topic = idea.get("topic", "").strip() or "Tópico sem título"
        logger.info("✅ Tópico: %s", topic)

        # 2) Gerar copy visual (curto e impactante)
        logger.info("🎨 Criando copy visual...")
        visual = llm.generate_visual_copy(topic=topic)
        
        # 3) Gerar legenda Instagram (separado do visual)
        logger.info("✍️ Escrevendo legenda...")
        caption_obj = llm.write_post_caption(topic=topic)
        caption = (caption_obj.get("caption") or "").strip()
        hashtags = caption_obj.get("hashtags") or []
        
        if isinstance(hashtags, list) and hashtags:
            hashtags_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
            full_caption = f"{caption}\n\n{hashtags_str}".strip()
        else:
            full_caption = caption

        # 4) Buscar imagem de fundo no Pexels
        logger.info("📸 Buscando imagem no Pexels...")
        pexels_query = visual.get("pexels_query", "professional business meeting")
        bg_path = pexels.get_background_for_query(pexels_query)
        
        # Se não achou no Pexels, usa gradiente (fallback)
        if bg_path and bg_path.exists():
            bg_url = f"file://{bg_path.resolve()}"
        else:
            logger.warning("⚠️ Pexels não retornou imagem, usando gradiente")
            bg_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1080' height='1350'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0%25' style='stop-color:%231e1b4b'/%3E%3Cstop offset='100%25' style='stop-color:%234338ca'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1080' height='1350' fill='url(%23g)'/%3E%3C/svg%3E"
        
        # Logo (opcional)
        logo_url = None
        if settings.LOGO_PATH.exists():
            logo_url = f"file://{settings.LOGO_PATH.resolve()}"

        # 5) Renderizar HTML → JPG
        logger.info("🖼️ Renderizando HTML para imagem...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = settings.PROCESSED_DIR / f"post_html_{ts}.jpg"

        template_data = {
            "kicker": visual.get("kicker", "Inovação & Educação"),
            "title": visual.get("title", topic),
            "subtitle": visual.get("subtitle", "Tecnologia que transforma"),
            "cta": visual.get("cta", "Link na bio"),
            "background_url": bg_url,
            "logo_url": logo_url,
            "ig_handle": "@eduflow.ia",
        }

        await renderer.render_post(
            template_name="post_eduflow.html",
            data=template_data,
            output_path=out_path,
            quality=95,
        )

        # 6) Salvar no banco
        logger.info("💾 Salvando no banco de dados...")
        metadata = {
            "idea": idea,
            "visual": visual,
            "caption_obj": caption_obj,
            "render_method": "html",
        }

        record = ContentRecord(
            content_type="post_html",
            platform=platform,
            topic=topic,
            caption=full_caption,
            asset_path=str(out_path),
            content_hash=compute_content_hash(topic=topic, caption=full_caption),
            status="rendered",
            metadata_json=repo.to_metadata_json(metadata),
        )
        repo.insert(record)

        logger.info("✅ Post HTML gerado com sucesso!")
        logger.info("📁 Arquivo: %s", out_path)
        return out_path

    except ContentDuplicateError as exc:
        logger.warning("⚠️ %s", exc)
        raise
    except Exception as exc:
        logger.exception("❌ Erro no pipeline HTML: %s", exc)
        raise


def main() -> None:
    setup_logging(level="INFO")
    settings.ensure_directories()

    try:
        niche = "como agentes de IA podem ajudar instituições de ensino a melhorar atendimento e captação de alunos"
        
        # Roda a função async
        asyncio.run(generate_one_html_post(niche=niche, platform="instagram"))
        
    except ContentDuplicateError:
        logger.info("🔄 Execute novamente para gerar conteúdo diferente.")
    except Exception as exc:
        logger.error("❌ Erro fatal: %s", exc)
        raise


if __name__ == "__main__":
    main()