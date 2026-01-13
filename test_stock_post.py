import os
from dotenv import load_dotenv

from src.generators.stock_images import PexelsImageBank
from src.processors.image_editor import ImageEditor

load_dotenv()

pexels = PexelsImageBank(api_key=os.getenv("PEXELS_API_KEY", ""))
bg = pexels.download_first("estudante usando notebook estudando EAD")

editor = ImageEditor()
out = editor.create_post(
    image_path=bg,
    title="EAD Sem Segredos!",
    subtitle="Quebrando objeções comuns sobre o ensino a distância.",
    kicker="Quebrando objeções",
    output_path="assets/processed/post_stock.jpg",
    template="photo_overlay",
    logo_path="assets/raw/logo.png",
)

print("Gerado:", out)
