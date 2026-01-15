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

    try:
        data = file_path.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        logger.error(f"Erro ao ler arquivo para base64: {file_path} - {e}")
        return ""


def _inline_file_src(html: str) -> str:
    """Substitui todos os src="file://..." por data URIs inline"""

    def repl(match: re.Match) -> str:
        raw_path = match.group(1)
        # Remove file:// se estiver duplicado ou mal formatado e cria Path
        clean_path = raw_path.replace("file://", "")
        p = Path(clean_path)

        if not p.exists():
            logger.warning("⚠️ Arquivo local não encontrado para inline: %s", p)
            return match.group(0) # Retorna original se falhar

        # logger.info("📎 Convertendo para base64: %s", p.name)
        data_uri = _file_to_data_uri(p)
        if data_uri:
            return f'src="{data_uri}"'
        return match.group(0)

    return _FILE_SRC_RE.sub(repl, html)


class HtmlRenderer:
    """
    Renderiza posts usando HTML/CSS via Playwright.
    Converte file:// para base64 automaticamente para evitar erros de CORS/Path.
    """

    def __init__(self, templates_dir: Path | str = None) -> None:
        if templates_dir is None:
            # Garante que pega do settings ou usa padrão relativo
            root = getattr(settings, "PROJECT_ROOT", Path.cwd())
            templates_dir = root / "src" / "templates"

        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            # Cria a pasta se não existir para evitar crash imediato
            logger.warning(f"Pasta de templates não encontrada: {self.templates_dir}. Criando...")
            self.templates_dir.mkdir(parents=True, exist_ok=True)

        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        logger.info("✅ HtmlRenderer inicializado (templates: %s)", self.templates_dir)

    async def render_post(
        self,
        template_name: str,
        data: dict[str, Any],
        output_path: Path | str,
        width: int = 1080,
        height: int = 1080, # Padrão quadrado, mas aceita mudança
        quality: int = 95,
    ) -> Path:
        """
        Renderiza template HTML em imagem JPG.
        
        Args:
            template_name: Nome do arquivo .html em src/templates
            data: Dicionário com variáveis para o Jinja2
            output_path: Onde salvar o JPG
            width: Largura da viewport
            height: Altura da viewport
            quality: Qualidade do JPG (0-100)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1) Renderizar template (Jinja2)
        logger.info("📝 Processando template: %s", template_name)
        try:
            template = self.env.get_template(template_name)
            html_content = template.render(**data)
        except Exception as e:
            logger.error(f"❌ Erro ao processar Jinja2 template: {e}")
            raise

        # 2) Converter file:// para base64 (Fix para Playwright)
        html_content = _inline_file_src(html_content)

        # 3) Renderizar no Navegador (Playwright)
        logger.info("🎨 Renderizando pixels...")
        async with async_playwright() as p:
            # Lança browser
            browser = await p.chromium.launch(headless=True)
            
            # Configura página com Scale Factor alto para nitidez (Retina like)
            page = await browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=2, # 2 ou 3 melhora muito a qualidade do texto
            )

            # Carrega HTML
            await page.set_content(html_content, wait_until="networkidle")

            # Garante que fontes carregaram
            try:
                await page.evaluate("document.fonts.ready")
            except Exception:
                pass

            # Screenshot
            await page.screenshot(
                path=str(output_path),
                type="jpeg",
                quality=quality,
                full_page=False,
            )

            await browser.close()

        size_kb = output_path.stat().st_size / 1024
        logger.info(f"✅ Imagem salva: {output_path.name} ({size_kb:.1f} KB)")
        
        return output_path