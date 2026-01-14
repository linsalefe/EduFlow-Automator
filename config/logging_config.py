# config/logging_config.py
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import PROJECT_ROOT


LOGS_DIR = PROJECT_ROOT / "logs"


def setup_logging(level: str = "INFO") -> None:
    """
    Configura logging estruturado com:
    - Console (colorido)
    - Arquivo rotacionado (máx 10MB, 5 backups)
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Remove handlers existentes
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    
    # Formato estruturado
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    
    # Handler Console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt))
    
    # Handler Arquivo (rotacionado)
    file_handler = RotatingFileHandler(
        filename=LOGS_DIR / "eduflow.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))
    
    # Configura root logger
    root.setLevel(level)
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    
    # Silencia logs muito verbosos de bibliotecas
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("instagrapi").setLevel(logging.INFO)
    
    logging.info("=" * 60)
    logging.info("🚀 EduFlow Automator - Logging iniciado")
    logging.info("=" * 60)