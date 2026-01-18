#!/usr/bin/env python3
# clean_assets.py
"""
Limpa artes antigas para começar do zero.
Remove arquivos de assets/processed/ e assets/raw/backgrounds/
"""

import shutil
from pathlib import Path


def clean_processed():
    """Remove todas as artes geradas."""
    processed = Path("assets/processed")
    if processed.exists():
        count = len(list(processed.glob("*")))
        shutil.rmtree(processed)
        processed.mkdir(parents=True, exist_ok=True)
        print(f"✅ Removidos {count} arquivos de assets/processed/")
    else:
        processed.mkdir(parents=True, exist_ok=True)
        print("📁 Pasta assets/processed/ criada")


def clean_backgrounds():
    """Remove backgrounds baixados do Pexels."""
    backgrounds = Path("assets/raw/backgrounds")
    if backgrounds.exists():
        count = len(list(backgrounds.glob("*")))
        shutil.rmtree(backgrounds)
        backgrounds.mkdir(parents=True, exist_ok=True)
        print(f"✅ Removidos {count} arquivos de assets/raw/backgrounds/")
    else:
        backgrounds.mkdir(parents=True, exist_ok=True)
        print("📁 Pasta assets/raw/backgrounds/ criada")


def clean_temp():
    """Remove arquivos temporários (exceto sessão do Instagram)."""
    temp = Path("assets/temp")
    if temp.exists():
        for f in temp.glob("*"):
            # Preserva sessão do Instagram
            if "instagram" not in f.name.lower():
                f.unlink()
                print(f"   Removido: {f.name}")
    else:
        temp.mkdir(parents=True, exist_ok=True)
    print("✅ Pasta assets/temp/ limpa (sessão Instagram preservada)")


def main():
    print("=" * 50)
    print("🧹 LIMPEZA DE ASSETS - EDUFLOW AUTOMATOR")
    print("=" * 50)
    print()
    
    clean_processed()
    clean_backgrounds()
    clean_temp()
    
    print()
    print("=" * 50)
    print("✅ LIMPEZA CONCLUÍDA!")
    print("=" * 50)
    print()
    print("Próximos passos:")
    print("  1. Copie o novo template para src/templates/")
    print("  2. Execute: python scheduler.py")
    print()


if __name__ == "__main__":
    main()