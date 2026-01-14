# test_stock_post.py
import os
from dotenv import load_dotenv

from src.generators.pexels_client import PexelsClient
from src.processors.image_editor import ImageEditor

load_dotenv()

pexels = PexelsClient(api_key=os.getenv("PEXELS_API_KEY", ""))
bg = pexels.get_background_for_query("estudante usando notebook estudando EAD")

editor = ImageEditor()
out = editor.create_post(
    background_path=bg,
    title="EAD Sem Segredos!",
    subtitle="Quebrando objeções comuns sobre o ensino a distância.",
    kicker="Quebrando objeções",
    output_path="assets/processed/post_stock.jpg",
    template="estacio_like",
    add_logo=True,
)

print("Gerado:", out)