# src/processors/html_renderer.py
from __future__ import annotations

import base64
import logging
import mimetypes
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

from config import settings

logger = logging.getLogger("eduflow.html_renderer")


# Regex para encontrar src="file://..."
_FILE_SRC_RE = re.compile(r'src="file://([^"]+)"')


def _file_to_data_uri(file_path: Path) -> str:
    """Converte arquivo local em data URI base64"""
    mime, _ = mimetypes.guess_type(str(file_path))
    if not mime:
        mime = "application/octet-stream"

    data = file_path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _inline_file_src(html: str) -> str:
    """Substitui todos os src="file://..." por data URIs inline"""

    def repl(match: re.Match) -> str:
        raw_path = match.group(1)
        p = Path(raw_path)

        if not p.exists():
            logger.warning("⚠️ Arquivo local não encontrado: %s", p)
            return match.group(0)

        logger.info("📎 Convertendo para base64: %s", p.name)
        return f'src="{_file_to_data_uri(p)}"'

    return _FILE_SRC_RE.sub(repl, html)


class HtmlRenderer:
    """
    Renderiza posts usando HTML/CSS via Playwright.
    Converte file:// para base64 automaticamente.
    """

    def __init__(self, templates_dir: Path | str = None) -> None:
        if templates_dir is None:
            templates_dir = settings.PROJECT_ROOT / "src" / "templates"

        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise RuntimeError(f"Pasta de templates não existe: {self.templates_dir}")

        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        logger.info("✅ HtmlRenderer inicializado (templates: %s)", self.templates_dir)

    async def render_post(
        self,
        template_name: str,
        data: dict[str, Any],
        output_path: Path | str,
        width: int = 1080,
        height: int = 1350,
        quality: int = 95,
    ) -> Path:
        """
        Renderiza template HTML em imagem JPG.
        Converte automaticamente file:// para base64.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1) Renderizar template
        logger.info("📝 Renderizando template: %s", template_name)
        template = self.env.get_template(template_name)
        html_content = template.render(**data)

        # 2) ✅ FIX: Converter file:// para base64
        html_content = _inline_file_src(html_content)

        # 3) Converter para imagem
        logger.info("🎨 Convertendo HTML para imagem...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=3,  # ✅ Aumenta ainda mais a nitidez
            )

            # Carrega HTML
            await page.set_content(html_content, wait_until="networkidle")

            # Aguarda fontes e imagens
            await page.evaluate("document.fonts && document.fonts.ready")
            await page.wait_for_timeout(500)

            # Screenshot
            await page.screenshot(
                path=str(output_path),
                type="jpeg",
                quality=98,  # ✅ Qualidade fixa no máximo prático
                full_page=False,
            )

            await browser.close()

        logger.info(
            "✅ Imagem gerada: %s (%.1f KB)",
            output_path,
            output_path.stat().st_size / 1024,
        )
        return output_path
