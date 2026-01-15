# main_html.py
from __future__ import annotations

import asyncio
import logging
import base64
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

GENERIC_PEXELS = {
    "professional business meeting", "business meeting", "office meeting",
    "office", "meeting", "business",
}


def image_to_base64(path: Path) -> str | None:
    """Converte imagem local para Base64 para embutir no HTML."""
    if not path.exists():
        logger.warning(f"⚠️ Imagem não encontrada para Base64: {path}")
        return None
    try:
        with open(path, "rb") as img:
            encoded = base64.b64encode(img.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logger.error(f"Erro ao converter imagem: {e}")
        return None


def calculate_font_size_class(text: str) -> str:
    """Define a classe CSS baseada no tamanho do texto."""
    length = len(text)
    if length < 15: return "text-xl"
    if length < 25: return "text-lg"
    if length < 50: return "text-md"
    return "text-sm"


def normalize_headline(headline: str) -> str:
    """Garante caixa alta e remove espaços extras."""
    return (headline or "").strip().upper()


def normalize_subheadline(sub: str) -> str:
    s = (sub or "").strip()
    if s.endswith("."):
        s = s[:-1].strip()
    return s


def refine_pexels_query(topic: str, fallback: str) -> str:
    """Otimiza a busca no Pexels para garantir imagens 'Business/Tech'."""
    t = (topic or "").lower().strip()
    base = (fallback or "").strip()

    if not base or base.lower() in GENERIC_PEXELS or len(base.split()) < 3:
        if any(w in t for w in ["matrícula", "captação", "leads", "recrutamento"]):
            base = "university admissions office counselor laptop"
        elif any(w in t for w in ["atendimento", "suporte", "secretaria", "chat"]):
            base = "student services support agent headset computer"
        elif any(w in t for w in ["whatsapp", "chatbot", "agente", "inteligência artificial", "ia"]):
            base = "student using smartphone whatsapp chat"
        else:
            base = "university student laptop technology"

    must_have = ["right side", "copy space left", "vertical", "cinematic lighting", "office"]
    q = base
    q_low = q.lower()
    for tok in must_have:
        if tok not in q_low:
            q += f" {tok}"
    return q.strip()


async def generate_one_html_post(niche: str, platform: str = "instagram") -> Path:
    logger.info("📝 Iniciando pipeline HTML para nicho: %s", niche)

    repo = ContentRepository()
    llm = GeminiClient()
    pexels = PexelsClient()
    renderer = HtmlRenderer()

    try:
        # 1) Ideia
        logger.info("🤖 Gerando ideia de tópico...")
        ideas = llm.generate_topic_ideas(niche=niche, count=1)
        idea = ideas[0]
        topic = idea.get("topic", "").strip() or "Tópico sem título"
        logger.info("✅ Tópico: %s", topic)

        # 2) Copy visual
        logger.info("🎨 Criando copy visual...")
        visual = llm.generate_visual_copy(topic=topic)

        headline = normalize_headline(visual.get("headline", "MAIS MATRÍCULAS\nCOM IA"))
        subheadline = normalize_subheadline(
            visual.get("subheadline", "Atendimento 24/7 no WhatsApp com agentes inteligentes")
        )

        # 3) Legenda
        logger.info("✍️ Escrevendo legenda...")
        caption_obj = llm.write_post_caption(topic=topic)
        caption = (caption_obj.get("caption") or "").strip()
        hashtags = caption_obj.get("hashtags") or []

        if isinstance(hashtags, list) and hashtags:
            hashtags_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
            full_caption = f"{caption}\n\n{hashtags_str}".strip()
        else:
            full_caption = caption

        # 4) Fundo (Pexels)
        logger.info("📸 Buscando imagem no Pexels...")
        pexels_query = refine_pexels_query(topic, visual.get("pexels_query") or "")
        
        bg_path = None
        candidate = pexels.get_background_for_query(pexels_query)
        if candidate and candidate.exists():
            bg_path = candidate
        
        if bg_path and bg_path.exists():
            bg_url = f"file://{bg_path.resolve()}"
        else:
            bg_url = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1080&q=80"

        # 5) Assets (Logo e Tamanho de Fonte)
        logo_path_local = Path("assets/brand/lodo_sem_fundo.png")
        logo_b64 = image_to_base64(logo_path_local)
        
        size_class = calculate_font_size_class(headline)

        # 6) Render (AGORA COM WIDTH/HEIGHT)
        logger.info("🖼️ Renderizando HTML para imagem...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = settings.PROCESSED_DIR / f"post_html_{ts}.jpg"

        template_data = {
            "headline": headline,
            "subheadline": subheadline,
            "imagem_fundo": bg_url,
            "classe_tamanho_texto": size_class,
            "logo_path": logo_b64,
        }

        await renderer.render_post(
            template_name="post_estacio.html",
            data=template_data,
            output_path=out_path,
            width=1080,   # <--- GARANTINDO 1080x1080
            height=1080,  # <--- GARANTINDO 1080x1080
            quality=98,
        )

        # 7) Salvar no banco
        logger.info("💾 Salvando no banco de dados...")
        metadata = {"idea": idea, "visual": visual, "caption_obj": caption_obj, "render_method": "html"}

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

        logger.info("✅ Post HTML gerado com sucesso: %s", out_path)
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
        asyncio.run(generate_one_html_post(niche=niche, platform="instagram"))
    except ContentDuplicateError:
        logger.info("🔄 Execute novamente para gerar conteúdo diferente.")
    except Exception as exc:
        logger.error("❌ Erro fatal: %s", exc)
        raise


if __name__ == "__main__":
    main()