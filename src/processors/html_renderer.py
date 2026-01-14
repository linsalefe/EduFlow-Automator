# src/processors/html_renderer.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

from config import settings

logger = logging.getLogger("eduflow.html_renderer")


class HtmlRenderer:
    """
    Renderiza posts usando HTML/CSS via Playwright (Chromium).
    Qualidade profissional superior ao Pillow.
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
        Renderiza template HTML em imagem JPG de alta qualidade.
        
        Args:
            template_name: Nome do arquivo .html (ex: 'post_eduflow.html')
            data: Dicionário com variáveis do template
            output_path: Caminho onde salvar a imagem
            width: Largura da imagem (px)
            height: Altura da imagem (px)
            quality: Qualidade JPEG (1-100)
        
        Returns:
            Path da imagem gerada
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1) Renderizar template Jinja2
        logger.info("📝 Renderizando template: %s", template_name)
        template = self.env.get_template(template_name)
        html_content = template.render(**data)
        
        # 2) Converter HTML para imagem via Playwright
        logger.info("🎨 Convertendo HTML para imagem...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )
            
            # Carrega o HTML
            await page.set_content(html_content, wait_until="networkidle")
            
            # Aguarda fontes e imagens carregarem
            try:
                await page.wait_for_timeout(2000)  # 2 segundos para estabilizar
            except Exception:
                pass
            
            # Screenshot de alta qualidade
            await page.screenshot(
                path=str(output_path),
                type="jpeg",
                quality=quality,
                full_page=False,
            )
            
            await browser.close()
        
        logger.info("✅ Imagem gerada: %s (%.1f KB)", output_path, output_path.stat().st_size / 1024)
        return output_path