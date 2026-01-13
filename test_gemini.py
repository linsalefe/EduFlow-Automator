from src.generators.gemini_client import GeminiClient

client = GeminiClient()
ideas = client.generate_topic_ideas("captação de matrículas para faculdades EAD", count=2)
print(ideas)
