# test_fase1.py
"""Valida se FASE 1 foi concluída com sucesso"""

import sys
from pathlib import Path

def test_settings():
    print("🔍 Testando settings.py...")
    from config import settings
    
    assert hasattr(settings, 'PROMPT_SCRIPTS_VIDEO_PATH'), "❌ PROMPT_SCRIPTS_VIDEO_PATH não existe"
    assert hasattr(settings, 'PROMPT_CAPTIONS_POST_PATH'), "❌ PROMPT_CAPTIONS_POST_PATH não existe"
    assert hasattr(settings, 'CONTENT_LANGUAGE'), "❌ CONTENT_LANGUAGE não existe"
    assert settings.CONTENT_LANGUAGE == "pt-BR", "❌ CONTENT_LANGUAGE deveria ser pt-BR"
    
    print(f"  ✅ PROMPT_SCRIPTS_VIDEO_PATH: {settings.PROMPT_SCRIPTS_VIDEO_PATH}")
    print(f"  ✅ PROMPT_CAPTIONS_POST_PATH: {settings.PROMPT_CAPTIONS_POST_PATH}")
    print(f"  ✅ CONTENT_LANGUAGE: {settings.CONTENT_LANGUAGE}")


def test_pexels_import():
    print("\n🔍 Testando import PexelsClient...")
    from src.generators.pexels_client import PexelsClient
    print("  ✅ PexelsClient importado com sucesso")


def test_stock_images_deleted():
    print("\n🔍 Verificando se stock_images.py foi deletado...")
    stock_path = Path("src/generators/stock_images.py")
    assert not stock_path.exists(), "❌ stock_images.py ainda existe! Delete ele."
    print("  ✅ stock_images.py deletado corretamente")


def test_scheduler_import():
    print("\n🔍 Testando imports do scheduler.py...")
    try:
        from scheduler import _create_static_post, _create_video_mock
        print("  ✅ scheduler.py importado sem erros")
    except ImportError as e:
        print(f"  ❌ Erro no import: {e}")
        sys.exit(1)


def test_image_editor_signature():
    print("\n🔍 Testando assinatura do ImageEditor.create_post...")
    from src.processors.image_editor import ImageEditor
    import inspect
    
    sig = inspect.signature(ImageEditor.create_post)
    params = list(sig.parameters.keys())
    
    assert 'background_path' in params, "❌ background_path não existe"
    assert 'raw_image_path' not in params, "❌ raw_image_path ainda existe (deveria ter sido removido)"
    assert 'image_path' not in params, "❌ image_path ainda existe (deveria ter sido removido)"
    
    print("  ✅ Assinatura padronizada corretamente")
    print(f"  Parâmetros: {params}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE VALIDAÇÃO - FASE 1")
    print("=" * 60)
    
    try:
        test_settings()
        test_pexels_import()
        test_stock_images_deleted()
        test_scheduler_import()
        test_image_editor_signature()
        
        print("\n" + "=" * 60)
        print("✅ FASE 1 COMPLETA - Todas as correções aplicadas!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)