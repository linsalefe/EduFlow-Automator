# test_image_editor.py
from src.processors.image_editor import ImageEditor

editor = ImageEditor()

out = editor.create_post(
    title="EAD Sem Segredos!",
    subtitle="Descubra como estudar no seu ritmo sem cair em armadilhas comuns.",
    kicker="Quebrando objeções comuns sobre o ensino a distância…",
    raw_image_path=None,  # ou "assets/raw/backgrounds/sua_foto.jpg"
)

print("Gerado:", out)
