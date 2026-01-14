# src/generators/pexels_client.py
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests
from requests import Response
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings

logger = logging.getLogger("eduflow.pexels")


class PexelsError(RuntimeError):
    pass


@dataclass(frozen=True)
class PexelsPhoto:
    id: int
    width: int
    height: int
    photographer: str
    url: str
    src: dict[str, str]


class PexelsClient:
    BASE_URL = "https://api.pexels.com/v1"

    def __init__(self, api_key: Optional[str] = None, download_dir: Optional[Path] = None) -> None:
        settings.ensure_directories()
        self.api_key = (api_key or settings.PEXELS_API_KEY or "").strip()
        self.download_dir = download_dir or settings.BACKGROUNDS_DIR

        if not self.api_key:
            logger.warning("PEXELS_API_KEY vazio. PexelsClient não conseguirá baixar imagens.")

    def get_background_for_query(self, query: str) -> Optional[Path]:
        """
        Busca no Pexels uma foto vertical e faz cache em assets/raw/backgrounds.
        Retorna o caminho do arquivo baixado (ou existente no cache).
        """
        if not self.api_key:
            return None

        query = (query or "").strip()
        if not query:
            query = "education students laptop"

        try:
            photos = self.search_photos(query=query, per_page=20, orientation="portrait")
        except Exception as e:
            logger.exception("Falha ao buscar fotos no Pexels: %s", e)
            return None

        if not photos:
            logger.warning("Pexels: nenhuma foto encontrada para query='%s'", query)
            return None

        chosen = self._choose_best(photos)
        if not chosen:
            return None

        cached = self._cache_path(chosen.id)
        if cached.exists():
            logger.info("Pexels cache hit: %s", cached)
            return cached

        url = self._pick_best_src(chosen.src)
        if not url:
            logger.warning("Pexels: foto sem src válido (id=%s)", chosen.id)
            return None

        try:
            self._download_file(url=url, dest=cached)
            logger.info("Pexels background salvo: %s (id=%s)", cached, chosen.id)
            return cached
        except Exception as e:
            logger.exception("Falha ao baixar imagem Pexels: %s", e)
            return None

    def search_photos(self, query: str, per_page: int = 15, orientation: str = "portrait") -> list[PexelsPhoto]:
        data = self._get(
            "/search",
            params={
                "query": query,
                "per_page": max(1, min(per_page, 80)),
                "orientation": orientation,
            },
        )

        photos_raw = data.get("photos", []) if isinstance(data, dict) else []
        photos: list[PexelsPhoto] = []

        for p in photos_raw:
            try:
                photos.append(
                    PexelsPhoto(
                        id=int(p["id"]),
                        width=int(p.get("width", 0)),
                        height=int(p.get("height", 0)),
                        photographer=str(p.get("photographer", "")),
                        url=str(p.get("url", "")),
                        src=dict(p.get("src", {})),
                    )
                )
            except Exception:
                continue

        return photos

    # -----------------------
    # Internals
    # -----------------------
    def _cache_path(self, photo_id: int) -> Path:
        return self.download_dir / f"pexels_{photo_id}.jpg"

    def _pick_best_src(self, src: dict[str, str]) -> Optional[str]:
        # prioridade de qualidade
        for key in ("original", "large2x", "large", "portrait"):
            if key in src and src[key]:
                return src[key]
        # fallback: qualquer um
        for v in src.values():
            if v:
                return v
        return None

    def _choose_best(self, photos: list[PexelsPhoto]) -> Optional[PexelsPhoto]:
        """
        Pexels retorna ordenado por relevância.
        Primeira foto = melhor match com a query.
        """
        if not photos:
            return None

        # Filtra por tamanho adequado
        good = [p for p in photos if p.width >= 1200 and p.height >= 1600]
        if good:
            return good[0]  # ✅ PRIMEIRA (mais relevante)

        # Fallback: primeira mesmo assim
        return photos[0]
    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.2, min=1, max=8),
        retry=retry_if_exception_type((requests.RequestException, PexelsError)),
    )
    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if not self.api_key:
            raise PexelsError("PEXELS_API_KEY não configurada")

        url = f"{self.BASE_URL}{path}"
        headers = {"Authorization": self.api_key}

        resp = requests.get(url, headers=headers, params=params, timeout=30)
        self._raise_for_status(resp)

        data = resp.json()
        if not isinstance(data, dict):
            raise PexelsError("Resposta inesperada do Pexels")
        return data

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.2, min=1, max=8),
        retry=retry_if_exception_type((requests.RequestException, PexelsError)),
    )
    def _download_file(self, url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)

        headers = {"Authorization": self.api_key}
        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            self._raise_for_status(r)
            tmp = dest.with_suffix(".tmp")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
            tmp.replace(dest)

    def _raise_for_status(self, resp: Response) -> None:
        if resp.status_code == 429:
            raise PexelsError("Rate limit Pexels (429). Tente novamente em instantes.")
        if resp.status_code >= 400:
            raise PexelsError(f"Pexels HTTP {resp.status_code}: {resp.text[:200]}")
