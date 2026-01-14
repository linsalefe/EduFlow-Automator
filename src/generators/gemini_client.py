from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger("eduflow.gemini")


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model_name: str = "gemini-2.0-flash"  # default seguro conforme docs de migração
    temperature: float = 0.7
    max_output_tokens: int = 1200


class GeminiClient:
    def __init__(self, config: Optional[GeminiConfig] = None) -> None:
        api_key = (config.api_key if config else settings.GEMINI_API_KEY).strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY não configurada no .env")

        self.config = config or GeminiConfig(api_key=api_key)

        # Cliente novo (google-genai)
        self.client = genai.Client(api_key=self.config.api_key)

    def _read_prompt_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise RuntimeError(f"Prompt não encontrado: {path}") from exc
        except Exception as exc:
            raise RuntimeError(f"Erro lendo prompt {path}: {exc}") from exc

    @retry(wait=wait_exponential(min=1, max=12), stop=stop_after_attempt(3))
    def _generate_text(self, prompt: str) -> str:
        try:
            resp = self.client.models.generate_content(
                model=self.config.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_output_tokens,
                ),
            )
            text = (resp.text or "").strip()
            if not text:
                raise RuntimeError("Gemini retornou resposta vazia.")
            return text
        except Exception as exc:
            logger.exception("Erro na chamada Gemini: %s", exc)
            raise

    def generate_topic_ideas(self, niche: str, count: int = 6) -> list[dict[str, Any]]:
        prompt = (
            "Você é um estrategista de conteúdo para Instagram e TikTok.\n"
            "Gere ideias de tópicos altamente práticos e virais.\n"
            "Responda SOMENTE em JSON válido.\n\n"
            f"Nicho: {niche}\n"
            f"Quantidade: {count}\n\n"
            "Formato de saída (array JSON):\n"
            '[{"topic":"...", "angle":"...", "hook":"...", "target":"..."}]'
        )

        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, list):
            raise RuntimeError("Formato inesperado: Gemini não retornou uma lista JSON.")
        return parsed

    def write_video_script(self, topic: str, duration_sec: int = 30) -> dict[str, Any]:
        prompt_template = self._read_prompt_file(settings.PROMPT_SCRIPTS_VIDEO_PATH)

        prompt = (
            f"{prompt_template}\n\n"
            "Responda SOMENTE em JSON válido.\n"
            "Formato:\n"
            '{"topic":"...", "duration_sec": 30, "hook":"...", "beats":[...], "cta":"..."}\n\n'
            f"Tópico: {topic}\n"
            f"Duração (segundos): {duration_sec}\n"
        )

        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, dict):
            raise RuntimeError("Formato inesperado: Gemini não retornou um objeto JSON para roteiro.")
        return parsed

    def write_post_caption(self, topic: str) -> dict[str, Any]:
        prompt_template = self._read_prompt_file(settings.PROMPT_CAPTIONS_POST_PATH)

        prompt = (
            f"{prompt_template}\n\n"
            "Responda SOMENTE em JSON válido.\n"
            "Formato:\n"
            '{"topic":"...", "title":"...", "caption":"...", "hashtags":["..."]}\n\n'
            f"Tópico: {topic}\n"
            f"Idioma: {settings.CONTENT_LANGUAGE}\n"
        )

        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, dict):
            raise RuntimeError("Formato inesperado: Gemini não retornou um objeto JSON para legenda.")
        return parsed
    
    def generate_bullets(self, topic: str, count: int = 4) -> list[str]:
        """
        Gera bullets/pontos-chave sobre um tópico.
        Útil para slides de carrossel.
        """
        prompt = (
            "Você é um especialista em conteúdo educacional.\n"
            "Gere pontos-chave (bullets) concisos e práticos.\n"
            "Responda SOMENTE em JSON válido.\n\n"
            f"Tópico: {topic}\n"
            f"Quantidade de bullets: {count}\n\n"
            "Formato de saída (array JSON):\n"
            '["Ponto 1", "Ponto 2", "Ponto 3", ...]'
        )

        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, list):
            raise RuntimeError("Formato inesperado: Gemini não retornou uma lista JSON para bullets.")
        
        return parsed[:count]  # garante o limite

    def write_carousel_caption(
        self,
        topic: str,
        hook: str = "",
        bullets: Optional[list[str]] = None,
    ) -> str:
        """
        Gera uma legenda otimizada para carrossel do Instagram.
        Mais curta que post normal, foca em CTA para deslizar.
        """
        bullets_text = ""
        if bullets:
            bullets_text = "\n".join([f"- {b}" for b in bullets])

        prompt = (
            "Você é um copywriter de Instagram especializado em carrosséis.\n"
            "Crie uma legenda CURTA e objetiva (máximo 3 parágrafos).\n"
            "Inclua:\n"
            "- Hook forte no início\n"
            "- Menção aos pontos do carrossel\n"
            "- CTA para deslizar e salvar o post\n"
            "- 5 a 8 hashtags relevantes\n\n"
            f"Tópico: {topic}\n"
            f"Hook: {hook}\n"
            f"Pontos-chave:\n{bullets_text}\n\n"
            "Responda APENAS a legenda pronta (texto puro, sem JSON)."
        )

        caption = self._generate_text(prompt)
        return caption.strip()

    def generate_visual_copy(self, topic: str) -> dict[str, Any]:
        """
        Gera copy ULTRA CURTO para design visual impactante.
        Inspirado em Estácio, Kroton, Uninter.
        """
        prompt = (
            "Você é um designer de posts para Instagram de grandes marcas educacionais.\n"
            "Crie textos EXTREMAMENTE CURTOS e impactantes.\n\n"
            f"Tópico: {topic}\n\n"
            "REGRAS RÍGIDAS:\n"
            "1. 'title': Máximo 5 palavras. SEM explicações. SEM frases completas. Apenas IMPACTO.\n"
            "   Exemplos BONS: 'IA na Educação', 'Futuro é Agora', 'Transforme sua IES'\n"
            "   Exemplos RUINS: 'Agentes de IA para Educação: Simplificando...'\n"
            "2. 'subtitle': Máximo 8 palavras. Complementa o título.\n"
            "3. 'kicker': 2-3 palavras de categoria (ex: Tecnologia & Inovação)\n"
            "4. 'cta': 2-3 palavras (ex: Saiba mais, Fale conosco)\n"
            "5. 'pexels_query': Termo em INGLÊS que GARANTA foto com PESSOAS (ex: 'happy university students smiling group')\n\n"
            "Responda SOMENTE em JSON válido:\n"
            '{\n'
            '  "kicker": "...",\n'
            '  "title": "...",\n'
            '  "subtitle": "...",\n'
            '  "cta": "...",\n'
            '  "pexels_query": "..."\n'
            '}'
        )

        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini não retornou dict JSON para visual_copy.")
        
        # Valida tamanhos
        title = parsed.get("title", "")
        if len(title.split()) > 6:
            logger.warning("⚠️ Título muito longo (%d palavras), truncando", len(title.split()))
            parsed["title"] = " ".join(title.split()[:5])
        
        return parsed
    
    def _safe_json_loads(self, raw: str) -> Any:
        cleaned = raw.strip()

        # remove fences comuns ```json ... ```
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()

        # tenta recortar do primeiro {/[ até o último }/]
        start_candidates = [cleaned.find("["), cleaned.find("{")]
        start_candidates = [i for i in start_candidates if i != -1]
        if start_candidates:
            start = min(start_candidates)
            end = max(cleaned.rfind("]"), cleaned.rfind("}"))
            if end != -1 and end > start:
                cleaned = cleaned[start : end + 1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Falha ao parsear JSON do Gemini. Raw:\n%s", raw)
            raise RuntimeError(f"Gemini retornou JSON inválido: {exc}") from exc
