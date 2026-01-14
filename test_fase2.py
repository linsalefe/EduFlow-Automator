# test_fase2.py
"""Valida se FASE 2 foi concluída com sucesso"""

import sys
import inspect

def test_image_editor_carousel():
    print("🔍 Testando ImageEditor.create_carousel...")
    from src.processors.image_editor import ImageEditor
    
    assert hasattr(ImageEditor, 'create_carousel'), "❌ create_carousel não existe"
    
    sig = inspect.signature(ImageEditor.create_carousel)
    params = list(sig.parameters.keys())
    
    assert 'slides' in params, "❌ parâmetro 'slides' não existe"
    assert 'background_path' in params, "❌ parâmetro 'background_path' não existe"
    assert 'basename' in params, "❌ parâmetro 'basename' não existe"
    
    print("  ✅ create_carousel implementado corretamente")
    print(f"  Parâmetros: {params}")


def test_gemini_bullets():
    print("\n🔍 Testando GeminiClient.generate_bullets...")
    from src.generators.gemini_client import GeminiClient
    
    assert hasattr(GeminiClient, 'generate_bullets'), "❌ generate_bullets não existe"
    
    sig = inspect.signature(GeminiClient.generate_bullets)
    params = list(sig.parameters.keys())
    
    assert 'topic' in params, "❌ parâmetro 'topic' não existe"
    assert 'count' in params, "❌ parâmetro 'count' não existe"
    
    print("  ✅ generate_bullets implementado corretamente")
    print(f"  Parâmetros: {params}")


def test_gemini_carousel_caption():
    print("\n🔍 Testando GeminiClient.write_carousel_caption...")
    from src.generators.gemini_client import GeminiClient
    
    assert hasattr(GeminiClient, 'write_carousel_caption'), "❌ write_carousel_caption não existe"
    
    sig = inspect.signature(GeminiClient.write_carousel_caption)
    params = list(sig.parameters.keys())
    
    assert 'topic' in params, "❌ parâmetro 'topic' não existe"
    assert 'hook' in params, "❌ parâmetro 'hook' não existe"
    assert 'bullets' in params, "❌ parâmetro 'bullets' não existe"
    
    print("  ✅ write_carousel_caption implementado corretamente")
    print(f"  Parâmetros: {params}")


def test_instagram_carousel():
    print("\n🔍 Testando InstagramPublisher.publish_carousel...")
    from src.publishers.instagram_api import InstagramPublisher
    
    assert hasattr(InstagramPublisher, 'publish_carousel'), "❌ publish_carousel não existe"
    
    sig = inspect.signature(InstagramPublisher.publish_carousel)
    params = list(sig.parameters.keys())
    
    assert 'image_paths' in params, "❌ parâmetro 'image_paths' não existe"
    assert 'caption' in params, "❌ parâmetro 'caption' não existe"
    
    print("  ✅ publish_carousel implementado corretamente")
    print(f"  Parâmetros: {params}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE VALIDAÇÃO - FASE 2")
    print("=" * 60)
    
    try:
        test_image_editor_carousel()
        test_gemini_bullets()
        test_gemini_carousel_caption()
        test_instagram_carousel()
        
        print("\n" + "=" * 60)
        print("✅ FASE 2 COMPLETA - Todos os métodos implementados!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)