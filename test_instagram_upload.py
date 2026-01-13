from pathlib import Path
from src.publishers.instagram_api import InstagramPublisher

publisher = InstagramPublisher()

image = Path("assets/processed/post_20260113_114412.jpg")  # troque para um existente
caption = "Teste automático EduFlow Automator 🚀"

media_id = publisher.publish_photo(image, caption)
print("Publicado:", media_id)
