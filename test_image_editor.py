# test_image_editor.py
from src.processors.image_editor import ImageEditor

editor = ImageEditor()

out = editor.create_post(
    title="EAD Sem Segredos!",
    subtitle="Descubra como estudar no seu ritmo sem cair em armadilhas comuns.",
    kicker="Quebrando objeções comuns sobre o ensino a distância…",
    background_query="university students studying laptop modern",
    auto_fetch_background=True,
    template="estacio_like",
    add_logo=True,
)

print("Gerado:", out)