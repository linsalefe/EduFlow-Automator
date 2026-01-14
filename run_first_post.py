# run_first_post.py
"""Gera o primeiro post real do EduFlow Automator"""

from config.logging_config import setup_logging
from main import generate_one_static_post

if __name__ == "__main__":
    setup_logging(level="INFO")
    
    print("=" * 60)
    print("🎨 GERANDO PRIMEIRO POST REAL")
    print("=" * 60)
    
    # Nicho específico da EduFlow IA
    niche = "como agentes de IA podem ajudar instituições de ensino a melhorar atendimento e captação de alunos"
    
    try:
        post_path = generate_one_static_post(niche=niche, platform="instagram")
        
        print("\n" + "=" * 60)
        print(f"✅ POST GERADO COM SUCESSO!")
        print(f"📁 Arquivo: {post_path}")
        print("=" * 60)
        print("\n📋 Próximos passos:")
        print("1. Abra a imagem gerada")
        print("2. Revise o conteúdo")
        print("3. Se estiver OK, use test_instagram_upload.py para publicar")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\n💡 Verifique se:")
        print("  - GEMINI_API_KEY está configurada no .env")
        print("  - PEXELS_API_KEY está configurada no .env")
        print("  - Você tem internet")