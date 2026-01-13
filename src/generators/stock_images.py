from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("eduflow.stock_images")


@dataclass(frozen=True)
class PexelsConfig:
    api_key: str
    base_url: str = "https://api.pexels.com/v1"


class PexelsImageBank:
    """
    Baixa imagens do Pexels para usar como fundo dos posts.
    Docs: https://www.pexels.com/api/documentation/
    """

    def __init__(self, api_key: str, timeout_s: int = 30) -> None:
        self.cfg = PexelsConfig(api_key=api_key)
        self.timeout_s = timeout_s

    def download_first(
        self,
        query: str,
        out_dir: str = "assets/raw/stock",
        orientation: str = "portrait",
        size: str = "large",
    ) -> str:
        """
        Faz search e baixa a primeira imagem encontrada.
        Retorna o caminho do arquivo salvo.
        """
        out_path_dir = Path(out_dir)
        out_path_dir.mkdir(parents=True, exist_ok=True)

        try:
            url = f"{self.cfg.base_url}/search"
            headers = {"Authorization": self.cfg.api_key}
            params = {
                "query": query,
                "per_page": 1,
                "orientation": orientation,
                "size": size,
            }

            resp = requests.get(url, headers=headers, params=params, timeout=self.timeout_s)
            resp.raise_for_status()

            data = resp.json()
            photos = data.get("photos", [])
            if not photos:
                raise RuntimeError(f"Nenhuma imagem encontrada no Pexels para: {query}")

            photo = photos[0]
            src = photo.get("src", {})
            # melhor opção para fundo
            img_url = src.get("portrait") or src.get("large2x") or src.get("large") or src.get("original")
            if not img_url:
                raise RuntimeError("Resposta do Pexels sem URL de imagem.")

            filename = f"pexels_{photo.get('id','img')}.jpg"
            out_path = out_path_dir / filename

            self._download_file(img_url, out_path)
            logger.info("✅ Imagem baixada do Pexels: %s", out_path.as_posix())
            return out_path.as_posix()

        except Exception as e:
            logger.exception("❌ Falha ao baixar imagem do Pexels: %s", e)
            raise

    def _download_file(self, url: str, out_path: Path) -> None:
        r = requests.get(url, stream=True, timeout=self.timeout_s)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
