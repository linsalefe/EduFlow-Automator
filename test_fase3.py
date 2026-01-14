# test_fase3.py
"""Teste completo da FASE 3: Logging + Exceções + Documentação"""

import sys
import logging
from pathlib import Path

def test_logging_config():
    print("🔍 Testando sistema de logging...")
    from config.logging_config import setup_logging, LOGS_DIR
    
    # Configura logging
    setup_logging(level="INFO")
    
    # Verifica se pasta de logs existe
    assert LOGS_DIR.exists(), "❌ Pasta logs/ não foi criada"
    
    # Testa logging
    logger = logging.getLogger("test")
    logger.info("✅ Teste de log INFO")
    logger.warning("⚠️ Teste de log WARNING")
    
    # Verifica se arquivo de log foi criado
    log_file = LOGS_DIR / "eduflow.log"
    assert log_file.exists(), "❌ Arquivo eduflow.log não foi criado"
    
    print(f"  ✅ Logging configurado corretamente")
    print(f"  ✅ Logs em: {log_file}")


def test_custom_exceptions():
    print("\n🔍 Testando exceções customizadas...")
    from src.exceptions import (
        EduFlowError,
        ContentDuplicateError,
        GeminiAPIError,
        PexelsAPIError,
        InstagramAPIError,
        ConfigurationError,
        AssetNotFoundError,
    )
    
    # Testa herança
    assert issubclass(ContentDuplicateError, EduFlowError), "❌ Herança incorreta"
    assert issubclass(GeminiAPIError, EduFlowError), "❌ Herança incorreta"
    
    # Testa raise
    try:
        raise ContentDuplicateError("Teste de duplicata")
    except ContentDuplicateError as e:
        assert "duplicata" in str(e).lower(), "❌ Mensagem incorreta"
    
    print("  ✅ Todas as exceções funcionando")
    print("  ✅ Herança correta")


def test_repository_exceptions():
    print("\n🔍 Testando exceções no Repository...")
    from database.repository import ContentRepository, ContentRecord, compute_content_hash
    from database.init_db import init_db
    from config.settings import DB_PATH
    from src.exceptions import ContentDuplicateError
    
    # Inicializa DB
    init_db(DB_PATH)
    repo = ContentRepository()
    
    # Cria registro teste
    test_hash = compute_content_hash("Fase3 Test", "Caption Fase3")
    
    record = ContentRecord(
        content_type="post",
        platform="instagram",
        topic="Fase3 Test",
        caption="Caption Fase3",
        asset_path="/fake/fase3.jpg",
        content_hash=test_hash,
        status="test",
    )
    
    # Primeira inserção: OK
    try:
        repo.insert(record)
        print("  ✅ Primeira inserção funcionou")
    except ContentDuplicateError:
        print("  ℹ️ Registro já existe (executou antes)")
    
    # Segunda inserção: deve lançar ContentDuplicateError
    try:
        repo.insert(record)
        print("  ❌ ERRO: Deveria ter lançado ContentDuplicateError!")
        sys.exit(1)
    except ContentDuplicateError:
        print("  ✅ ContentDuplicateError lançada corretamente")


def test_documentation():
    print("\n🔍 Testando documentação...")
    
    readme = Path("README.md")
    assert readme.exists(), "❌ README.md não existe"
    
    content = readme.read_text(encoding="utf-8")
    assert "EduFlow Automator" in content, "❌ Título faltando"
    assert "eduflowia.com" in content, "❌ Link do site faltando"
    assert "@eduflow.ia" in content, "❌ Instagram handle faltando"
    assert "agentes de IA" in content, "❌ Descrição do negócio faltando"
    
    print("  ✅ README.md completo")
    print(f"  ✅ Tamanho: {len(content)} caracteres")


def test_logs_directory_structure():
    print("\n🔍 Testando estrutura de pastas...")
    from config.settings import ensure_directories
    
    ensure_directories()
    
    required_dirs = [
        Path("assets/raw"),
        Path("assets/processed"),
        Path("assets/temp"),
        Path("database"),
        Path("logs"),
        Path("prompts"),
    ]
    
    for d in required_dirs:
        assert d.exists(), f"❌ Diretório {d} não existe"
    
    print("  ✅ Todas as pastas criadas")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE FINAL - FASE 3")
    print("=" * 60)
    
    try:
        test_logging_config()
        test_custom_exceptions()
        test_repository_exceptions()
        test_documentation()
        test_logs_directory_structure()
        
        print("\n" + "=" * 60)
        print("✅ FASE 3 COMPLETA - Sistema profissional!")
        print("=" * 60)
        print("\n📊 Resumo:")
        print("  ✅ Logging estruturado com rotação")
        print("  ✅ Exceções customizadas")
        print("  ✅ Tratamento robusto de erros")
        print("  ✅ Documentação completa")
        print("  ✅ Estrutura de pastas organizada")
        
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)