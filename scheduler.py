# scheduler.py
"""
Scheduler do EduFlow Automator.
Gera e publica posts automaticamente a cada 2 horas, 24/7.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime

import schedule

from config import settings
from config.logging_config import setup_logging
from main_html import generate_and_publish

logger = logging.getLogger("eduflow.scheduler")


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Intervalo entre posts (em minutos para teste)
POST_INTERVAL_MINUTES = 5

# Nichos para variar o conteúdo
NICHOS = [
    "conversão de leads em matrículas para faculdades",
    "atendimento automatizado 24/7 para instituições de ensino",
    "como IA ajuda equipes comerciais de faculdades",
    "qualificação automática de leads educacionais",
    "follow-up inteligente para recuperar leads frios",
    "integração de IA com CRM para escolas",
    "redução de tempo de resposta em secretarias acadêmicas",
    "como não perder leads fora do horário comercial",
    "automação do atendimento via WhatsApp para cursos",
    "resultados reais de IA na educação",
]


# ============================================================
# JOB PRINCIPAL
# ============================================================

def job_generate_and_publish():
    """Job que gera e publica um post."""
    logger.info("=" * 60)
    logger.info(f"⏰ Scheduler executando - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Seleciona nicho aleatório para variar conteúdo
    niche = random.choice(NICHOS)
    logger.info(f"📌 Nicho selecionado: {niche}")
    
    # Tenta até 3 vezes (caso gere duplicado)
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            success = asyncio.run(generate_and_publish(niche=niche))
            
            if success:
                logger.info("✅ Post publicado com sucesso!")
                return
            else:
                logger.warning(f"⚠️ Tentativa {attempt}/{max_attempts} falhou, tentando novamente...")
                # Muda o nicho para próxima tentativa
                niche = random.choice(NICHOS)
                time.sleep(5)
                
        except Exception as exc:
            logger.exception(f"❌ Erro na tentativa {attempt}: {exc}")
            time.sleep(10)
    
    logger.error("❌ Todas as tentativas falharam")


def job_health_check():
    """Log de health check a cada hora."""
    logger.info(f"💓 Health check - Sistema rodando - {datetime.now().strftime('%H:%M')}")


# ============================================================
# SCHEDULER
# ============================================================

def run_scheduler():
    """Inicia o scheduler 24/7."""
    logger.info("=" * 60)
    logger.info("🚀 EDUFLOW AUTOMATOR - SCHEDULER INICIADO")
    logger.info(f"📅 Intervalo: 1 post a cada {POST_INTERVAL_MINUTES} minutos")
    logger.info(f"🕐 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Agenda posts a cada 2 horas
    schedule.every(POST_INTERVAL_MINUTES).minutes.do(job_generate_and_publish)
    
    # Health check a cada hora
    schedule.every(1).hours.do(job_health_check)
    
    # Executa primeiro post imediatamente
    logger.info("🎬 Executando primeiro post agora...")
    job_generate_and_publish()
    
    # Loop infinito
    logger.info(f"⏳ Próximo post em {POST_INTERVAL_MINUTES} minutos...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Checa a cada minuto


# ============================================================
# MODO MANUAL (para testes)
# ============================================================

def run_once():
    """Executa apenas uma vez (para teste)."""
    logger.info("🧪 Modo de teste - executando uma vez")
    job_generate_and_publish()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    setup_logging(level="INFO")
    settings.ensure_directories()
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Modo teste: python scheduler.py --once
        run_once()
    else:
        # Modo produção: python scheduler.py
        run_scheduler()