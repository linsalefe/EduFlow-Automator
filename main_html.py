# main_html.py
"""
Orquestrador principal do EduFlow Automator.
Gera posts HTML profissionais e publica no Instagram.
"""

from __future__ import annotations

import asyncio
import logging
import base64
import random
from datetime import datetime
from pathlib import Path

from config import settings
from config.logging_config import setup_logging
from database.repository import ContentRecord, ContentRepository, compute_content_hash
from src.exceptions import ContentDuplicateError
from src.generators.gemini_client import GeminiClient
from src.generators.pexels_client import PexelsClient
from src.processors.html_renderer import HtmlRenderer

logger = logging.getLogger("eduflow.main")


# ============================================================
# CONFIGURAÇÕES DO POST
# ============================================================

TEMPLATE_NAME = "post_eduflow_v2.html"

# Badges rotativos para variar os posts
BADGES = [
    "Case de Sucesso",
    "Resultado Real", 
    "Dica Prática",
    "Tendência 2025",
    "Insight",
    "Novidade",
]

# CTAs rotativos
CTAS = [
    "Saiba mais no link da bio",
    "Link na bio",
    "Agende uma demo grátis",
    "Fale com a gente",
]

# Queries otimizadas para Pexels (pessoas de frente, sorridentes, profissionais)
PEXELS_QUERIES = {
    "atendimento": [
        "customer service woman smiling headset office",
        "support agent happy computer professional",
        "call center woman friendly headphones",
    ],
    "estudante": [
        "happy university student laptop smiling",
        "college student woman studying happy",
        "young professional student laptop cafe smiling",
    ],
    "gestor": [
        "business woman office smiling confident",
        "professional manager tablet happy",
        "executive woman meeting smiling",
    ],
    "equipe": [
        "team meeting happy office collaboration",
        "business team smiling modern office",
        "colleagues working together happy",
    ],
    "tecnologia": [
        "professional woman smartphone happy modern",
        "young business person laptop smiling",
        "woman using phone office happy",
    ],
    "default": [
        "happy professional woman office laptop",
        "smiling business person modern workspace",
        "confident professional woman technology",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def image_to_base64(path: Path) -> str | None:
    """Converte imagem local para Base64."""
    if not path or not path.exists():
        return None
    try:
        with open(path, "rb") as img:
            encoded = base64.b64encode(img.read()).decode('utf-8')
        ext = path.suffix.lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        return f"data:{mime};base64,{encoded}"
    except Exception as e:
        logger.error(f"Erro ao converter imagem: {e}")
        return None


def get_font_size_class(text: str) -> str:
    """Define classe CSS baseada no tamanho do texto."""
    # Remove tags HTML para contar caracteres
    clean = text.replace("<span class='highlight'>", "").replace("<span class='highlight-blue'>", "").replace("</span>", "")
    length = len(clean)
    
    if length < 30:
        return ""  # Tamanho padrão (72px)
    if length < 50:
        return "text-lg"  # 64px
    if length < 70:
        return "text-md"  # 56px
    return "text-sm"  # 48px


def select_pexels_query(topic: str) -> str:
    """Seleciona query do Pexels baseada no tópico."""
    topic_lower = topic.lower()
    
    if any(w in topic_lower for w in ["atendimento", "suporte", "chat", "whatsapp", "resposta"]):
        queries = PEXELS_QUERIES["atendimento"]
    elif any(w in topic_lower for w in ["aluno", "estudante", "matrícula", "curso"]):
        queries = PEXELS_QUERIES["estudante"]
    elif any(w in topic_lower for w in ["gestor", "diretor", "coordenador", "gestão"]):
        queries = PEXELS_QUERIES["gestor"]
    elif any(w in topic_lower for w in ["equipe", "time", "comercial", "vendas"]):
        queries = PEXELS_QUERIES["equipe"]
    elif any(w in topic_lower for w in ["tecnologia", "ia", "automação", "digital"]):
        queries = PEXELS_QUERIES["tecnologia"]
    else:
        queries = PEXELS_QUERIES["default"]
    
    return random.choice(queries)


def format_headline(headline: str) -> str:
    """
    Formata headline para HTML, adicionando destaque em números e palavras-chave.
    """
    # Palavras que devem ser destacadas em amarelo
    highlight_words = ["+340%", "340%", "24/7", "24h", "100%", "2 min", "2min", "zero"]
    
    # Palavras que devem ser destacadas em azul
    highlight_blue = ["IA", "WhatsApp", "CRM"]
    
    result = headline
    
    for word in highlight_words:
        if word.lower() in result.lower():
            # Preserva o case original
            import re
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            result = pattern.sub(f"<span class='highlight'>{word}</span>", result)
    
    for word in highlight_blue:
        if word in result:
            result = result.replace(word, f"<span class='highlight-blue'>{word}</span>")
    
    # Converte \n para <br>
    result = result.replace("\\n", "<br>").replace("\n", "<br>")
    
    return result


def clean_subheadline(text: str) -> str:
    """Limpa e formata subheadline."""
    text = (text or "").strip()
    # Remove ponto final se houver
    if text.endswith("."):
        text = text[:-1]
    # Corrige "capte" para "converta" se escapou
    text = text.replace("Capte", "Converta").replace("capte", "converta")
    text = text.replace("captação", "conversão").replace("Captação", "Conversão")
    return text


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

async def generate_post(niche: str, platform: str = "instagram") -> Path:
    """
    Pipeline completo de geração de post:
    1. Gemini → ideia de tópico
    2. Gemini → copy visual (headline + subheadline)
    3. Gemini → legenda completa
    4. Pexels → foto de fundo
    5. HTML Renderer → imagem final
    6. SQLite → salvar histórico
    """
    logger.info("=" * 60)
    logger.info("🚀 Iniciando geração de post")
    logger.info("=" * 60)

    repo = ContentRepository()
    llm = GeminiClient()
    pexels = PexelsClient()
    renderer = HtmlRenderer()

    try:
        # 1) Gerar ideia de tópico
        logger.info("🤖 Gerando ideia de tópico...")
        ideas = llm.generate_topic_ideas(niche=niche, count=1)
        idea = ideas[0]
        topic = idea.get("topic", "").strip() or "IA para instituições de ensino"
        hook = idea.get("hook", "")
        logger.info(f"✅ Tópico: {topic}")

        # 2) Gerar copy visual
        logger.info("🎨 Gerando copy visual...")
        visual = llm.generate_visual_copy(topic=topic)
        
        headline_raw = visual.get("headline", "CONVERTA\nMAIS\nLEADS")
        headline = format_headline(headline_raw)
        
        subheadline = clean_subheadline(
            visual.get("subheadline", "Atendimento 24/7 que transforma interessados em matrículas")
        )
        
        logger.info(f"✅ Headline: {headline_raw}")

        # 3) Gerar legenda completa
        logger.info("✍️ Gerando legenda...")
        caption_obj = llm.write_post_caption(topic=topic)
        caption = (caption_obj.get("caption") or "").strip()
        hashtags = caption_obj.get("hashtags") or []

        if isinstance(hashtags, list) and hashtags:
            hashtags_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
            full_caption = f"{caption}\n\n{hashtags_str}".strip()
        else:
            full_caption = caption

        # 4) Buscar foto no Pexels
        logger.info("📸 Buscando foto no Pexels...")
        pexels_query = select_pexels_query(topic)
        logger.info(f"   Query: {pexels_query}")
        
        bg_path = pexels.get_background_for_query(pexels_query)
        
        if bg_path and bg_path.exists():
            bg_url = f"file://{bg_path.resolve()}"
            logger.info(f"✅ Foto encontrada: {bg_path.name}")
        else:
            # Fallback para imagem genérica
            bg_url = "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=1080&q=80"
            logger.warning("⚠️ Usando foto fallback do Unsplash")

        # 5) Preparar assets
        logo_path = Path("assets/brand/lodo_sem_fundo.png")
        if not logo_path.exists():
            logo_path = settings.LOGO_PATH
        logo_b64 = image_to_base64(logo_path)

        badge_text = random.choice(BADGES)
        cta_text = random.choice(CTAS)
        size_class = get_font_size_class(headline)

        # 6) Renderizar HTML
        logger.info("🖼️ Renderizando imagem...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = settings.PROCESSED_DIR / f"post_{ts}.jpg"

        template_data = {
            "imagem_fundo": bg_url,
            "logo_path": logo_b64,
            "headline": headline,
            "subheadline": subheadline,
            "badge_text": badge_text,
            "cta_text": cta_text,
            "classe_tamanho_texto": size_class,
        }

        await renderer.render_post(
            template_name=TEMPLATE_NAME,
            data=template_data,
            output_path=out_path,
            width=1080,
            height=1080,
            quality=95,
        )

        logger.info(f"✅ Imagem gerada: {out_path}")

        # 7) Salvar no banco
        logger.info("💾 Salvando no banco de dados...")
        content_hash = compute_content_hash(topic=topic, caption=full_caption)
        
        metadata = {
            "idea": idea,
            "visual": visual,
            "caption_obj": caption_obj,
            "template": TEMPLATE_NAME,
            "pexels_query": pexels_query,
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

        logger.info("=" * 60)
        logger.info("✅ POST GERADO COM SUCESSO!")
        logger.info(f"📁 Arquivo: {out_path}")
        logger.info("=" * 60)

        return out_path

    except ContentDuplicateError as exc:
        logger.warning(f"⚠️ Conteúdo duplicado: {exc}")
        raise
    except Exception as exc:
        logger.exception(f"❌ Erro no pipeline: {exc}")
        raise


# ============================================================
# PUBLICAÇÃO NO INSTAGRAM
# ============================================================

async def generate_and_publish(niche: str) -> bool:
    """
    Gera um post e publica no Instagram.
    Retorna True se publicou com sucesso.
    """
    from src.publishers.instagram_api import InstagramPublisher
    
    repo = ContentRepository()
    
    try:
        # Gerar post
        post_path = await generate_post(niche=niche, platform="instagram")
        
        # Buscar legenda do banco
        # (simplificado - pega do último registro)
        import sqlite3
        with sqlite3.connect(settings.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT caption, content_hash FROM content_history WHERE asset_path = ? LIMIT 1",
                (str(post_path),)
            )
            row = cur.fetchone()
        
        if not row:
            logger.error("❌ Não encontrou registro no banco")
            return False
        
        caption, content_hash = row
        
        # Publicar
        logger.info("📤 Publicando no Instagram...")
        publisher = InstagramPublisher()
        media_id = publisher.publish_photo(image_path=post_path, caption=caption)
        
        # Marcar como publicado
        repo.mark_published(content_hash, platform_id=media_id, platform="instagram")
        
        logger.info(f"✅ Publicado com sucesso! media_id={media_id}")
        return True
        
    except ContentDuplicateError:
        logger.warning("⚠️ Conteúdo duplicado, tentando novamente...")
        return False
    except Exception as exc:
        logger.exception(f"❌ Erro ao publicar: {exc}")
        return False


# ============================================================
# ENTRY POINT
# ============================================================

def main() -> None:
    """Executa uma geração de post."""
    setup_logging(level="INFO")
    settings.ensure_directories()
    
    # Nicho principal
    niche = "conversão de leads em matrículas para instituições de ensino com IA"
    
    try:
        asyncio.run(generate_post(niche=niche, platform="instagram"))
    except ContentDuplicateError:
        logger.info("🔄 Execute novamente para gerar conteúdo diferente.")
    except Exception as exc:
        logger.error(f"❌ Erro fatal: {exc}")
        raise


if __name__ == "__main__":
    main()