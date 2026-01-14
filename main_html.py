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


GENERIC_PEXELS = {
    "professional business meeting",
    "business meeting",
    "office meeting",
    "office",
    "meeting",
    "business",
}


def normalize_headline(headline: str) -> str:
    """Garante caixa alta + quebra em linhas se vier tudo em uma linha."""
    text = (headline or "").strip().upper()

    if "\n" in text:
        return text

    # fallback: quebra 1-2 palavras por linha
    words = [w for w in text.split() if w]
    lines = []
    i = 0
    while i < len(words):
        chunk = words[i : i + 2]
        lines.append(" ".join(chunk))
        i += 2

    # limita a 5 linhas (Estácio-like)
    return "\n".join(lines[:5])


def normalize_subheadline(sub: str) -> str:
    s = (sub or "").strip()
    # sem ponto final
    if s.endswith("."):
        s = s[:-1].strip()
    return s


def refine_pexels_query(topic: str, fallback: str) -> str:
    """
    Usa a query do Gemini como base (fallback) e só reforça composição:
    - assunto à direita
    - copy space à esquerda
    - vibe educação + IA
    """
    t = (topic or "").lower().strip()
    base = (fallback or "").strip()

    if not base or base.lower() in GENERIC_PEXELS or len(base.split()) < 3:
        # base por tema (bem mais "IA + educação")
        if any(w in t for w in ["matrícula", "captação", "leads", "recrutamento"]):
            base = "university admissions office counselor laptop"
        elif any(w in t for w in ["atendimento", "suporte", "secretaria", "chat"]):
            base = "student services support agent headset computer"
        elif any(w in t for w in ["whatsapp", "chatbot", "agente", "inteligência artificial", "ia"]):
            base = "student using smartphone whatsapp chat"
        else:
            base = "university student laptop technology"

    # reforços de composição (Pexels entende muito bem esses termos)
    must_have = [
        "right side",
        "copy space left",
        "vertical",
        "shallow depth of field",
        "cinematic lighting",
    ]
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

        headline = normalize_headline(visual.get("headline", "MAIS\nMATRÍCULAS\nCOM\nIA"))
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

        # 4) Fundo (Pexels) — agora com múltiplas tentativas
        logger.info("📸 Buscando imagem no Pexels...")
        pexels_query_raw = (visual.get("pexels_query") or "").strip() or "university student laptop"
        pexels_query = refine_pexels_query(topic, pexels_query_raw)
        logger.info("📸 Query Pexels (refinada): %s", pexels_query)

        # Múltiplas tentativas
        attempts = [
            pexels_query,
            pexels_query.replace("student using smartphone whatsapp chat", "student using laptop"),
            "university admissions office laptop right side copy space left vertical",
            "student services office headset right side copy space left vertical",
        ]

        bg_path = None
        for q in attempts:
            logger.info("📸 Tentando: %s", q)
            candidate = pexels.get_background_for_query(q)
            if candidate and candidate.exists():
                bg_path = candidate
                logger.info("✅ Imagem encontrada!")
                break

        if bg_path and bg_path.exists():
            bg_url = f"file://{bg_path.resolve()}"
        else:
            logger.warning("⚠️ Pexels não retornou imagem, usando gradiente")
            bg_url = (
                "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1080' height='1350'%3E"
                "%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='0' y2='1'%3E"
                "%3Cstop offset='0%25' style='stop-color:%231e1b4b'/%3E"
                "%3Cstop offset='100%25' style='stop-color:%234338ca'/%3E"
                "%3C/linearGradient%3E%3C/defs%3E"
                "%3Crect width='1080' height='1350' fill='url(%23g)'/%3E%3C/svg%3E"
            )

        # 5) Render
        logger.info("🖼️ Renderizando HTML para imagem...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = settings.PROCESSED_DIR / f"post_html_{ts}.jpg"

        template_data = {
            "headline": headline,
            "subheadline": subheadline,
            "imagem_fundo": bg_url,
        }

        await renderer.render_post(
            template_name="post_estacio_like.html",
            data=template_data,
            output_path=out_path,
            quality=98,
        )

        # 6) Salvar no banco
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
        asyncio.run(generate_one_html_post(niche=niche, platform="instagram"))
    except ContentDuplicateError:
        logger.info("🔄 Execute novamente para gerar conteúdo diferente.")
    except Exception as exc:
        logger.error("❌ Erro fatal: %s", exc)
        raise


if __name__ == "__main__":
    main()