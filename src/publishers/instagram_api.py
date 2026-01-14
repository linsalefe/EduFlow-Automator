from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, LoginRequired, TwoFactorRequired

from config import settings

logger = logging.getLogger("eduflow.instagram")


@dataclass(frozen=True)
class InstagramCredentials:
    username: str
    password: str


class InstagramPublisher:
    """
    Publicador Instagram usando instagrapi.
    - Reaproveita sessão salva em arquivo (evita login em todo run).
    - Aceita múltiplos nomes de env/settings:
      INSTAGRAM_PASSWORD/INSTAGRAM_PASS e INSTAGRAM_USER/INSTAGRAM_USERNAME.
    """

    def __init__(
        self,
        creds: Optional[InstagramCredentials] = None,
        session_path: Optional[Union[str, Path]] = None,
    ) -> None:
        # Compat: aceita diferentes nomes em settings.py
        username = getattr(settings, "INSTAGRAM_USER", "") or getattr(settings, "INSTAGRAM_USERNAME", "")
        password = getattr(settings, "INSTAGRAM_PASSWORD", "") or getattr(settings, "INSTAGRAM_PASS", "")

        self.creds = creds or InstagramCredentials(username=username, password=password)

        if not self.creds.username or not self.creds.password:
            raise RuntimeError(
                "Credenciais Instagram não configuradas. "
                "Defina no .env: INSTAGRAM_USER e INSTAGRAM_PASSWORD (ou INSTAGRAM_PASS)."
            )

        # session_path pode vir como str (do settings). Garantimos Path sempre.
        default_session = getattr(settings, "INSTAGRAM_SESSION_PATH", "assets/temp/instagram_session.json")
        chosen = session_path if session_path is not None else default_session
        self.session_path: Path = chosen if isinstance(chosen, Path) else Path(chosen)

        self.client = Client()

    def login(self) -> None:
        """
        Faz login e reaproveita sessão salva.
        """
        try:
            settings.ensure_directories()

            # tenta carregar sessão salva
            if self.session_path.exists():
                try:
                    self.client.load_settings(str(self.session_path))
                    logger.info("🔁 Sessão carregada: %s", self.session_path)
                except Exception:
                    logger.warning("Não foi possível carregar sessão. Fazendo login do zero.")

            # tenta validar sessão (sem login)
            try:
                self.client.get_timeline_feed()
                logger.info("✅ Sessão válida (sem precisar login).")
                return
            except Exception:
                pass

            # login normal
            logger.info("🔐 Fazendo login no Instagram...")
            self.client.login(self.creds.username, self.creds.password)

            # salva sessão
            self.session_path.parent.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(str(self.session_path))
            logger.info("✅ Login OK. Sessão salva em: %s", self.session_path)

        except TwoFactorRequired:
            logger.error("⚠️ Instagram pediu 2FA (TwoFactorRequired). Você precisa completar o fluxo de 2FA.")
            raise
        except ChallengeRequired:
            logger.error("⚠️ Instagram pediu Challenge (ChallengeRequired). Pode precisar confirmar via app/email.")
            raise
        except LoginRequired:
            logger.error("❌ LoginRequired. Credenciais inválidas ou sessão expirada.")
            raise
        except Exception as exc:
            logger.exception("❌ Falha no login Instagram: %s", exc)
            raise

    def publish_photo(self, image_path: Path, caption: str) -> str:
        """
        Publica uma foto no feed.
        Retorna media_id como string.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        try:
            self.login()
            logger.info("📤 Publicando foto: %s", image_path)

            media = self.client.photo_upload(path=str(image_path), caption=caption)
            media_id = str(media.id)

            logger.info("✅ Publicado com sucesso (media_id=%s)", media_id)
            return media_id

        except Exception as exc:
            logger.exception("❌ Falha ao publicar foto: %s", exc)
            raise
    def publish_carousel(self, image_paths: list[Path], caption: str) -> str:
        """
        Publica um carrossel (álbum) no feed.
        Retorna media_id como string.
        """
        if not image_paths:
            raise ValueError("image_paths não pode ser vazio")
        
        # Valida que todos os arquivos existem
        for path in image_paths:
            if not path.exists():
                raise FileNotFoundError(f"Imagem não encontrada: {path}")
        
        try:
            self.login()
            logger.info("📤 Publicando carrossel com %d imagens", len(image_paths))
            
            # Converte Path para string
            paths_str = [str(p) for p in image_paths]
            
            media = self.client.album_upload(paths=paths_str, caption=caption)
            media_id = str(media.id)
            
            logger.info("✅ Carrossel publicado com sucesso (media_id=%s)", media_id)
            return media_id
            
        except Exception as exc:
            logger.exception("❌ Falha ao publicar carrossel: %s", exc)
            raise
