# src/processors/image_editor.py
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import settings
from src.generators.pexels_client import PexelsClient

logger = logging.getLogger("eduflow.image_editor")


@dataclass(frozen=True)
class PostCopy:
    kicker: str
    title: str
    subtitle: str


class ImageEditor:
    """
    Templates profissionais para Instagram feed 1080x1350.
    Design inspirado em grandes marcas educacionais (Estácio, Uninter).
    """

    def __init__(self) -> None:
        settings.ensure_directories()
        self.pexels = PexelsClient()

    def create_post(
        self,
        title: str,
        subtitle: Optional[str] = None,
        kicker: Optional[str] = None,
        background_path: Optional[str | Path] = None,
        background_query: Optional[str] = None,
        auto_fetch_background: bool = True,
        output_path: Optional[str | Path] = None,
        add_logo: bool = True,
        template: str = "estacio_like",
        ig_handle: str = "@eduflow.ia",
    ) -> Path:
        settings.ensure_directories()
        copy = self._normalize_copy(title=title, subtitle=subtitle, kicker=kicker)

        bg = self._build_background(
            background_path=background_path,
            background_query=background_query or self._smart_query(title),
            auto_fetch=auto_fetch_background,
        )

        canvas = bg.convert("RGBA")
        draw = ImageDraw.Draw(canvas)

        if template == "minimal":
            self._render_minimal(canvas, draw, copy, add_logo=add_logo, ig_handle=ig_handle)
        else:
            self._render_estacio_like(canvas, draw, copy, add_logo=add_logo, ig_handle=ig_handle)

        out = self._resolve_output_path(output_path)
        self._save_jpeg_high(canvas, out)
        logger.info("✅ Post gerado: %s", out.as_posix())
        return out

    # -----------------------
    # Render: ESTACIO LIKE (PROFISSIONAL)
    # -----------------------
    def _render_estacio_like(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, copy: PostCopy, add_logo: bool, ig_handle: str) -> None:
        w, h = settings.POST_SIZE
        m = settings.SAFE_MARGIN

        # 1) Header mais discreto e elegante (100px ao invés de 140px)
        header_h = 100
        header = self._gradient_rgba(w, header_h, settings.GRADIENT_A, settings.GRADIENT_B, alpha=240)
        header = Image.alpha_composite(header, Image.new("RGBA", (w, header_h), (0, 0, 0, 30)))
        canvas.alpha_composite(header, (0, 0))

        # Logo + branding compacto
        x = m - 10
        y = 18
        if add_logo:
            x = self._paste_logo_plain(canvas, x=x, y=y, max_size=70) + 16

        brand_font = self._load_font(settings.FONT_EXTRABOLD, 42)
        brand_text = "EduFlow"
        brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
        brand_w = brand_bbox[2] - brand_bbox[0]

        self._draw_text_with_shadow(draw, (x, 32), brand_text, brand_font, settings.COLOR_WHITE, 110)

        ia_font = self._load_font(settings.FONT_EXTRABOLD, 42)
        ia_text = "IA"
        ia_x = x + brand_w + 5
        self._draw_text_with_shadow(draw, (ia_x, 32), ia_text, ia_font, settings.COLOR_ACCENT, 110)

        handle_font = self._load_font(settings.FONT_MEDIUM, 22)
        self._draw_text_with_shadow(draw, (w - m - 200, 44), ig_handle, handle_font, "#DDE0FF", 90)

        # 2) Card começa MAIS CEDO (deixa foto respirar - 45% ao invés de 58%)
        card_y = int(h * 0.45)
        card_w = w - (m * 2)
        card_h = h - card_y - m - 20

        self._glass_card(
            canvas=canvas,
            x=m,
            y=card_y,
            width=card_w,
            height=card_h,
            radius=28,
            blur_radius=14,
            fill_rgba=(15, 23, 42, 180),
            stroke_rgba=(129, 140, 248, 100),
            shadow=True,
        )

        # 3) Texto MAIS COMPACTO e elegante
        inner_x = m + 36
        inner_w = card_w - 72

        # Kicker menor e discreto
        kicker_font = self._load_font(settings.FONT_SEMIBOLD, 24)
        self._draw_wrapped_text(
            draw=draw,
            text=copy.kicker,
            font=kicker_font,
            x=inner_x,
            y=card_y + 32,
            max_width=inner_w,
            fill=settings.COLOR_ACCENT,
            line_spacing=6,
            shadow=True,
            shadow_alpha=100,
        )

        # Título MENOR (68px max ao invés de 92px)
        title_font = self._fit_font(
            font_path=settings.FONT_EXTRABOLD,
            text=copy.title,
            max_width=inner_w,
            start_size=68,
            min_size=44,
            max_lines=3,
        )
        title_y = card_y + 68
        title_lines = self._wrap_text(copy.title, title_font, inner_w)
        title_block_h = self._measure_multiline_height(title_lines, title_font, line_spacing=10)

        self._draw_wrapped_text(
            draw=draw,
            text=copy.title,
            font=title_font,
            x=inner_x,
            y=title_y,
            max_width=inner_w,
            fill=settings.COLOR_WHITE,
            line_spacing=10,
            shadow=True,
            shadow_alpha=140,
        )

        # Subtítulo MENOR e máximo 2 linhas
        sub_font = self._fit_font(
            font_path=settings.FONT_MEDIUM,
            text=copy.subtitle,
            max_width=inner_w,
            start_size=32,
            min_size=22,
            max_lines=2,
        )
        sub_y = title_y + title_block_h + 14
        self._draw_wrapped_text(
            draw=draw,
            text=copy.subtitle,
            font=sub_font,
            x=inner_x,
            y=sub_y,
            max_width=inner_w,
            fill="#E7E9FF",
            line_spacing=8,
            shadow=True,
            shadow_alpha=100,
        )

        # CTA discreto
        cta_font = self._load_font(settings.FONT_SEMIBOLD, 24)
        cta_text = "👉 Saiba mais no link da bio"
        cta_y = card_y + card_h - 54
        self._draw_text_with_shadow(draw, (inner_x, cta_y), cta_text, cta_font, "#F1F5FF", 120)

    # -----------------------
    # Render: MINIMAL (fallback)
    # -----------------------
    def _render_minimal(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, copy: PostCopy, add_logo: bool, ig_handle: str) -> None:
        w, h = settings.POST_SIZE
        m = settings.SAFE_MARGIN

        top_y = m
        if add_logo:
            _ = self._paste_logo_plain(canvas, x=m, y=top_y, max_size=110)

        tag_font = self._load_font(settings.FONT_SEMIBOLD, 28)
        self._draw_text_with_shadow(draw, (w - m - 240, m + 10), ig_handle, tag_font, "#DDE0FF", 110)

        content_x = m
        content_w = w - (m * 2)

        kicker_font = self._load_font(settings.FONT_SEMIBOLD, 34)
        kicker_y = int(h * 0.62)
        self._draw_wrapped_text(draw, copy.kicker, kicker_font, content_x, kicker_y, content_w, settings.COLOR_ACCENT, 10, True, 110)

        title_font = self._fit_font(settings.FONT_EXTRABOLD, copy.title, content_w, 110, 64, max_lines=3)
        title_y = kicker_y + 52
        self._draw_wrapped_text(draw, copy.title, title_font, content_x, title_y, content_w, settings.COLOR_WHITE, 14, True, 160)

        sub_font = self._fit_font(settings.FONT_MEDIUM, copy.subtitle, content_w, 44, 28, max_lines=3)
        sub_y = title_y + 180
        self._draw_wrapped_text(draw, copy.subtitle, sub_font, content_x, sub_y, content_w, "#E7E9FF", 10, True, 120)

    # -----------------------
    # Background / Pexels
    # -----------------------
    def pick_random_background(self) -> Optional[Path]:
        files: list[Path] = []
        if settings.BACKGROUNDS_DIR.exists():
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                files.extend(list(settings.BACKGROUNDS_DIR.glob(ext)))
        return random.choice(files) if files else None

    def create_carousel(
        self,
        slides: list[dict],
        background_path: Optional[str | Path] = None,
        background_query: Optional[str] = None,
        auto_fetch_background: bool = True,
        output_dir: Optional[str | Path] = None,
        basename: str = "carousel",
        template_default: str = "estacio_like",
        add_logo: bool = True,
        ig_handle: str = "@eduflow.ia",
    ) -> list[Path]:
        """Gera múltiplas imagens para carrossel do Instagram."""
        settings.ensure_directories()
        
        if not slides:
            raise ValueError("slides não pode ser vazio")
        
        out_dir = Path(output_dir) if output_dir else settings.PROCESSED_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        
        paths: list[Path] = []
        
        for i, slide in enumerate(slides, start=1):
            template = slide.get("template", template_default)
            kicker = slide.get("kicker", "")
            title = slide.get("title", "")
            subtitle = slide.get("subtitle", "")
            
            out_path = out_dir / f"{basename}_{i:03d}.jpg"
            
            path = self.create_post(
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                background_path=background_path,
                background_query=background_query,
                auto_fetch_background=auto_fetch_background,
                output_path=out_path,
                add_logo=add_logo,
                template=template,
                ig_handle=ig_handle,
            )
            
            paths.append(path)
            logger.info("✅ Slide %d/%d gerado: %s", i, len(slides), path)
        
        return paths

    def _smart_query(self, title: str) -> str:
        """
        Query otimizada para Pexels - busca fotos PROFISSIONAIS com PESSOAS.
        Inspirado em contas premium (Estácio, Uninter, Kroton).
        """
        title_lower = title.lower()
        
        # Atendimento/Suporte/Chat
        if any(word in title_lower for word in ["atendimento", "suporte", "chat", "chatbot", "whatsapp"]):
            return "smiling customer service woman headset modern office professional"
        
        # Estudantes/Alunos/Matrícula
        if any(word in title_lower for word in ["aluno", "estudante", "matrícula", "captação", "leads"]):
            return "happy college students laptop modern campus smiling group"
        
        # Professores/Docentes
        if any(word in title_lower for word in ["professor", "docente", "ensino", "aula"]):
            return "professional teacher classroom technology smiling confident"
        
        # Gestão/Administração
        if any(word in title_lower for word in ["gestão", "administração", "coordenação", "diretor"]):
            return "professional business meeting office teamwork collaboration happy"
        
        # Tecnologia/IA/Digital
        if any(word in title_lower for word in ["tecnologia", "ia", "inteligência artificial", "digital", "automação", "agente"]):
            return "professional young person laptop technology smiling modern bright office"
        
        # EAD/Online/Remoto
        if any(word in title_lower for word in ["ead", "online", "distância", "remoto", "home"]):
            return "young professional studying laptop home modern bright smiling"
        
        # Fallback: universitários felizes
        return "happy university students group laptop modern campus smiling diverse"

    def _build_background(self, background_path: Optional[str | Path], background_query: str, auto_fetch: bool) -> Image.Image:
        """
        Monta o background com overlays profissionais.
        Resultado: foto suavizada com gradiente sutil.
        """
        w, h = settings.POST_SIZE

        chosen: Optional[Path] = None
        if background_path:
            p = Path(background_path)
            if p.exists():
                chosen = p

        if not chosen:
            chosen = self.pick_random_background()

        if not chosen and auto_fetch:
            chosen = self.pexels.get_background_for_query(background_query)

        if chosen and chosen.exists():
            img = Image.open(chosen).convert("RGB")
            img = self._cover_resize(img, w, h)

            # Blur SUAVE (mantém rostos reconhecíveis)
            img_blur = img.filter(ImageFilter.GaussianBlur(radius=3))
            base = img_blur.convert("RGBA")

            # Overlay escuro suave (deixa foto visível)
            base = Image.alpha_composite(base, Image.new("RGBA", (w, h), (0, 0, 0, 85)))
            
            # Gradiente SUTIL (não mata a foto)
            base = Image.alpha_composite(base, self._gradient_rgba(w, h, settings.GRADIENT_A, settings.GRADIENT_B, alpha=70))
            
            # Highlight blob discreto
            base = Image.alpha_composite(base, self._highlight_blob(w, h))
            return base

        # Fallback: gradiente puro
        base = self._gradient_rgba(w, h, settings.GRADIENT_A, settings.GRADIENT_B, alpha=255)
        base = Image.alpha_composite(base, self._highlight_blob(w, h))
        base = Image.alpha_composite(base, Image.new("RGBA", (w, h), (0, 0, 0, 35)))
        return base

    # -----------------------
    # Glass card
    # -----------------------
    def _glass_card(
        self,
        canvas: Image.Image,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int,
        blur_radius: int,
        fill_rgba: tuple[int, int, int, int],
        stroke_rgba: tuple[int, int, int, int],
        shadow: bool = True,
    ) -> None:
        # blur local do fundo
        region = canvas.crop((x, y, x + width, y + height)).filter(ImageFilter.GaussianBlur(blur_radius))
        canvas.paste(region, (x, y))

        # sombra
        if shadow:
            sh = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh)
            sd.rounded_rectangle((0, 0, width, height), radius=radius, fill=(0, 0, 0, 140))
            sh = sh.filter(ImageFilter.GaussianBlur(18))
            canvas.alpha_composite(sh, (x + 8, y + 14))

        # card
        card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, width, height), radius=radius, fill=fill_rgba)
        cd.rounded_rectangle((2, 2, width - 2, height - 2), radius=radius - 2, outline=stroke_rgba, width=3)

        # brilho leve no topo do card
        cd.line([(28, 18), (width - 28, 18)], fill=(255, 255, 255, 55), width=2)

        canvas.alpha_composite(card, (x, y))

    # -----------------------
    # Logo (retorna próximo x)
    # -----------------------
    def _paste_logo_plain(self, canvas: Image.Image, x: int, y: int, max_size: int = 110) -> int:
        if not settings.LOGO_PATH.exists():
            logger.warning("Logo não encontrada em %s (pulando).", settings.LOGO_PATH)
            return x

        logo = Image.open(settings.LOGO_PATH).convert("RGBA")
        logo = self._contain_resize(logo, max_w=max_size, max_h=max_size)

        alpha = logo.split()[-1]

        shadow = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        shadow.putalpha(alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
        shadow = self._tint_rgba(shadow, (0, 0, 0, 140))

        glow = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        glow.putalpha(alpha)
        glow = glow.filter(ImageFilter.GaussianBlur(radius=16))
        glow = self._tint_rgba(glow, self._hex_to_rgba(settings.COLOR_PRIMARY, 120))

        canvas.alpha_composite(glow, (x + 2, y + 4))
        canvas.alpha_composite(shadow, (x + 3, y + 8))
        canvas.alpha_composite(logo, (x, y))

        return x + logo.width

    # -----------------------
    # Save JPEG (alta qualidade)
    # -----------------------
    def _save_jpeg_high(self, img: Image.Image, out: Path) -> None:
        out.parent.mkdir(parents=True, exist_ok=True)
        rgb = img.convert("RGB")
        rgb.save(out, format="JPEG", quality=96, optimize=True, progressive=True, subsampling=0)

    # -----------------------
    # Helpers: copy / paths
    # -----------------------
    def _normalize_copy(self, title: str, subtitle: Optional[str], kicker: Optional[str]) -> PostCopy:
        t = (title or "").strip() or "Educação que transforma vidas"
        s = (subtitle or "").strip() or "Tecnologia a favor da sua instituição de ensino"
        k = (kicker or "").strip() or "Inovação & Educação"
        return PostCopy(kicker=k, title=t, subtitle=s)

    def _resolve_output_path(self, output_path: Optional[str | Path]) -> Path:
        if output_path:
            return Path(output_path)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return settings.PROCESSED_DIR / f"post_{ts}.jpg"

    # -----------------------
    # Typography helpers
    # -----------------------
    def _load_font(self, path: Path, size: int) -> ImageFont.FreeTypeFont:
        try:
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        except Exception:
            pass
        return ImageFont.load_default()

    def _fit_font(
        self,
        font_path: Path,
        text: str,
        max_width: int,
        start_size: int,
        min_size: int,
        max_lines: int = 3,
    ) -> ImageFont.FreeTypeFont:
        size = start_size
        while size >= min_size:
            font = self._load_font(font_path, size)
            lines = self._wrap_text(text, font, max_width)
            if len(lines) <= max_lines and all(self._text_width(line, font) <= max_width for line in lines):
                return font
            size -= 2
        return self._load_font(font_path, min_size)

    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""

        for w in words:
            test = (current + " " + w).strip()
            if self._text_width(test, font) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w

        if current:
            lines.append(current)
        return lines

    def _measure_multiline_height(self, lines: list[str], font: ImageFont.ImageFont, line_spacing: int) -> int:
        if not lines:
            return 0
        ascent, descent = font.getmetrics()
        line_h = ascent + descent
        return len(lines) * line_h + (len(lines) - 1) * line_spacing

    def _draw_wrapped_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        x: int,
        y: int,
        max_width: int,
        fill: str,
        line_spacing: int,
        shadow: bool,
        shadow_alpha: int,
    ) -> None:
        lines = self._wrap_text(text, font, max_width)
        ascent, descent = font.getmetrics()
        line_h = ascent + descent

        cy = y
        for line in lines:
            if shadow:
                self._draw_text_with_shadow(draw, (x, cy), line, font, fill, shadow_alpha)
            else:
                draw.text((x, cy), line, font=font, fill=fill)
            cy += line_h + line_spacing

    def _draw_text_with_shadow(
        self,
        draw: ImageDraw.ImageDraw,
        xy: tuple[int, int],
        text: str,
        font: ImageFont.ImageFont,
        fill: str,
        shadow_alpha: int,
    ) -> None:
        sx, sy = xy
        shadow_fill = (0, 0, 0, shadow_alpha)
        draw.text((sx + 2, sy + 2), text, font=font, fill=shadow_fill)
        draw.text((sx + 1, sy + 1), text, font=font, fill=shadow_fill)
        draw.text((sx + 2, sy), text, font=font, fill=shadow_fill)
        draw.text((sx, sy + 2), text, font=font, fill=shadow_fill)
        draw.text((sx, sy), text, font=font, fill=fill)

    def _text_width(self, text: str, font: ImageFont.ImageFont) -> int:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    # -----------------------
    # Image helpers
    # -----------------------
    def _cover_resize(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        w, h = img.size
        scale = max(target_w / w, target_h / h)
        nw, nh = int(w * scale), int(h * scale)
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - target_w) // 2
        top = (nh - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    def _contain_resize(self, img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        w, h = img.size
        scale = min(max_w / w, max_h / h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return img.resize((nw, nh), Image.Resampling.LANCZOS)

    def _gradient_rgba(self, w: int, h: int, hex_a: str, hex_b: str, alpha: int) -> Image.Image:
        a = self._hex_to_rgb(hex_a)
        b = self._hex_to_rgb(hex_b)

        base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = base.load()
        if px is None:
            return base

        for y in range(h):
            t = y / max(1, h - 1)
            r = int(a[0] * (1 - t) + b[0] * t)
            g = int(a[1] * (1 - t) + b[1] * t)
            bl = int(a[2] * (1 - t) + b[2] * t)
            for x in range(w):
                px[x, y] = (r, g, bl, alpha)
        return base

    def _highlight_blob(self, w: int, h: int) -> Image.Image:
        blob = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(blob)
        d.ellipse((int(w * 0.55), int(h * -0.10), int(w * 1.20), int(h * 0.55)), fill=(255, 255, 255, 45))
        d.ellipse((int(w * -0.20), int(h * 0.25), int(w * 0.55), int(h * 1.05)), fill=(129, 140, 248, 55))
        return blob.filter(ImageFilter.GaussianBlur(radius=60))

    def _hex_to_rgb(self, hx: str) -> tuple[int, int, int]:
        hx = hx.lstrip("#")
        return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))

    def _hex_to_rgba(self, hx: str, a: int) -> tuple[int, int, int, int]:
        r, g, b = self._hex_to_rgb(hx)
        return (r, g, b, a)

    def _tint_rgba(self, img: Image.Image, rgba: tuple[int, int, int, int]) -> Image.Image:
        r, g, b, a = rgba
        colored = Image.new("RGBA", img.size, (r, g, b, 0))
        alpha = img.split()[-1]
        colored.putalpha(alpha.point(lambda p: min(255, int(p * (a / 255)))))
        return colored
    