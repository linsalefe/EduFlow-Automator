# test_pexels.py
from src.generators.pexels_client import PexelsClient

client = PexelsClient()
path = client.get_background_for_query("students studying laptop")
print("Baixado:", path)
