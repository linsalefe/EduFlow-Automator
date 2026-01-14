# test_integration.py
"""Teste de integração sem chamar APIs externas"""

import sys
from pathlib import Path

def test_database_flow():
    print("🔍 Testando fluxo de banco de dados...")
    from database.repository import ContentRepository, ContentRecord, compute_content_hash
    from database.init_db import init_db
    from config.settings import DB_PATH
    
    # Inicializa DB
    init_db(DB_PATH)
    
    repo = ContentRepository()
    
    # Cria registro teste
    test_hash = compute_content_hash("Teste Topic", "Teste Caption")
    
    record = ContentRecord(
        content_type="post",
        platform="instagram",
        topic="Teste Topic",
        caption="Teste Caption",
        asset_path="/fake/path.jpg",
        content_hash=test_hash,
        status="test",
    )
    
    # Insere
    content_id = repo.insert(record)
    print(f"  ✅ Registro inserido (id={content_id})")
    
    # Verifica duplicata
    assert repo.exists_by_hash(test_hash), "❌ Hash não encontrado"
    print(f"  ✅ Detecção de duplicata funcionando")
    
    # Marca como publicado
    repo.mark_published(test_hash, platform_id="12345", platform="instagram")
    print(f"  ✅ Marcado como publicado")


def test_image_editor_no_pexels():
    print("\n🔍 Testando ImageEditor sem Pexels...")
    from src.processors.image_editor import ImageEditor
    
    editor = ImageEditor()
    
    # Testa se consegue gerar gradiente (sem background)
    out = editor.create_post(
        title="Teste",
        subtitle="Subtítulo de teste",
        kicker="Kicker teste",
        auto_fetch_background=False,  # Não busca Pexels
        output_path="assets/processed/test_integration.jpg",
        template="estacio_like",
    )
    
    assert out.exists(), f"❌ Imagem não foi gerada: {out}"
    print(f"  ✅ Imagem gerada: {out}")
    print(f"  ✅ Tamanho: {out.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE INTEGRAÇÃO")
    print("=" * 60)
    
    try:
        test_database_flow()
        test_image_editor_no_pexels()
        
        print("\n" + "=" * 60)
        print("✅ INTEGRAÇÃO OK - Sistema funcionando!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)