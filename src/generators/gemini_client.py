# src/generators/gemini_client.py
"""
Cliente Gemini otimizado para EduFlow IA.
Prompts focados em captação de alunos para instituições de ensino.
"""

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


# ============================================================
# PROMPTS EMBUTIDOS (baseados nos arquivos de prompts/)
# ============================================================

SYSTEM_CONTEXT = """
Você trabalha para a EduFlow IA, empresa que desenvolve agentes de inteligência artificial para instituições de ensino.

SOBRE A EDUFLOW IA:
- Agentes de IA que convertem interessados em matrículas 24/7
- Atendimento instantâneo via WhatsApp, Instagram e Site
- Qualificação automática (separa curiosos de compradores reais)
- Integração com CRMs (RD Station, HubSpot, Salesforce)
- Follow-up automático para leads que esfriaram
- Transbordo para humano quando necessário

RESULTADOS COMPROVADOS (Case UNOPAR):
- +340% de aumento na conversão de matrículas via chat
- 8.500+ atendimentos por mês
- Resposta imediata (zero fila de espera)
- 100% dos leads registrados no CRM

PÚBLICO-ALVO:
- Gerentes comerciais de instituições de ensino
- Coordenadores de curso
- Diretores acadêmicos
- Donos de escolas e cursos

DORES DO PÚBLICO:
- Leads chegam mas não convertem (ficam sem resposta fora do horário)
- Equipe comercial sobrecarregada com perguntas repetitivas
- Não conseguem separar curiosos de interessados reais
- Demora no primeiro atendimento = lead foi pro concorrente
- Leads esfriam no funil por falta de follow-up
- Meta de matrículas não batida

TOM DE VOZ:
- Profissional mas acessível
- Consultor experiente, não vendedor
- Usa dados concretos, evita promessas vazias
- Foca em RESULTADOS, não em tecnologia
- Nunca usa jargões técnicos (ML, NLP, API)
"""


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.75
    max_output_tokens: int = 1500


class GeminiClient:
    def __init__(self, config: Optional[GeminiConfig] = None) -> None:
        api_key = (config.api_key if config else settings.GEMINI_API_KEY).strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY não configurada no .env")

        self.config = config or GeminiConfig(api_key=api_key)
        self.client = genai.Client(api_key=self.config.api_key)

    def _read_prompt_file(self, path: Path) -> str:
        """Lê arquivo de prompt se existir, senão retorna string vazia."""
        try:
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            logger.warning("Não foi possível ler prompt %s: %s", path, exc)
        return ""

    @retry(wait=wait_exponential(min=1, max=12), stop=stop_after_attempt(3))
    def _generate_text(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Chamada base ao Gemini com retry."""
        try:
            resp = self.client.models.generate_content(
                model=self.config.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature or self.config.temperature,
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

    # ============================================================
    # GERAÇÃO DE IDEIAS DE TÓPICOS
    # ============================================================
    def generate_topic_ideas(self, niche: str, count: int = 6) -> list[dict[str, Any]]:
        """
        Gera ideias de conteúdo focadas no nicho da EduFlow IA.
        
        Args:
            niche: Contexto adicional ou sub-nicho específico
            count: Quantidade de ideias para gerar
            
        Returns:
            Lista de dicts com: topic, angle, hook, target, category, emotion
        """
        prompt = f"""
{SYSTEM_CONTEXT}

## SUA MISSÃO
Gere {count} ideias de conteúdo para Instagram sobre: {niche}

As ideias devem:
1. Educar o mercado sobre IA na educação (sem ser técnico)
2. Gerar identificação com as dores do gestor educacional
3. Posicionar a EduFlow como autoridade
4. Despertar curiosidade

## CATEGORIAS (varie entre elas):
- Dor → Solução: problema comum e como IA resolve
- Mito vs Realidade: desmistificar IA na educação
- Dados & Tendências: estatísticas do setor
- Bastidores: como funciona um agente de IA
- Comparativo: Antes vs Depois de usar IA
- Objeções: responder dúvidas como "IA substitui pessoas?"

## FORMATO (JSON array):
[
  {{
    "topic": "Título curto e direto (max 80 chars)",
    "angle": "Ângulo específico do tema",
    "hook": "Frase de abertura que prende atenção",
    "target": "Cargo que mais se identifica",
    "category": "Uma das categorias acima",
    "emotion": "curiosidade | frustração | esperança | urgência"
  }}
]

Responda SOMENTE o JSON, sem explicações.
"""
        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, list):
            raise RuntimeError("Gemini não retornou lista JSON para ideias.")
        return parsed[:count]

    # ============================================================
    # ROTEIRO DE VÍDEO (REELS/TIKTOK)
    # ============================================================
    def write_video_script(self, topic: str, duration_sec: int = 30) -> dict[str, Any]:
        """
        Gera roteiro de vídeo curto para Reels/TikTok.
        
        Args:
            topic: Tópico do vídeo
            duration_sec: Duração alvo em segundos
            
        Returns:
            Dict com: topic, duration_sec, hook, beats, cta, visual_suggestion
        """
        prompt = f"""
{SYSTEM_CONTEXT}

## SUA MISSÃO
Crie um roteiro de vídeo curto ({duration_sec} segundos) para Instagram Reels.

TÓPICO: {topic}

## ESTRUTURA:
1. HOOK (0-3s): Primeira frase que decide se a pessoa assiste ou passa
   - Pergunta direta, dado chocante, ou cenário identificável
   
2. DESENVOLVIMENTO (3-20s): Máximo 3 pontos
   - Frases curtas (max 15 palavras cada)
   - Linguagem falada, não escrita
   
3. CTA (últimos 5s): Ação clara
   - "Link na bio", "Comenta EU QUERO", "Salva esse vídeo"

## FORMATO (JSON):
{{
  "topic": "{topic}",
  "duration_sec": {duration_sec},
  "hook": "Frase exata de abertura",
  "beats": [
    "Ponto 1: frase curta",
    "Ponto 2: frase curta",
    "Ponto 3: frase curta"
  ],
  "cta": "Chamada para ação",
  "visual_suggestion": "Como gravar (talking head, tela, b-roll)",
  "text_overlay": "Texto na tela durante hook (max 5 palavras)"
}}

Responda SOMENTE o JSON.
"""
        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini não retornou dict JSON para roteiro.")
        return parsed

    # ============================================================
    # LEGENDA DE POST
    # ============================================================
    def write_post_caption(self, topic: str) -> dict[str, Any]:
        """
        Gera legenda completa para post do Instagram.
        
        Args:
            topic: Tópico do post
            
        Returns:
            Dict com: topic, title, caption, hashtags, suggested_cta_type
        """
        prompt = f"""
{SYSTEM_CONTEXT}

## SUA MISSÃO
Crie uma legenda de Instagram sobre: {topic}

## ESTRUTURA:
1. GANCHO (primeira linha): Faz a pessoa clicar em "mais"
   - Pergunta provocativa, afirmação ousada, ou dado surpreendente
   
2. CORPO: Parágrafos curtos (2-3 linhas)
   - Desenvolva um argumento ou conte mini-história
   - Inclua pelo menos 1 dado/número concreto
   - Máximo 150 palavras
   
3. CTA: Termine com ação clara
   - "Link na bio", "Comenta QUERO", "Salva pra mostrar pro time"

## TOM:
- Consultor experiente compartilhando insight
- Profissional mas humano
- Evite ser vendedor ou guru de marketing

## FORMATO (JSON):
{{
  "topic": "{topic}",
  "title": "Título interno (max 60 chars)",
  "caption": "Legenda completa com \\n\\n entre parágrafos",
  "hashtags": ["educacao", "captacaodealunos", "iaparaeducacao", "..."],
  "suggested_cta_type": "link_bio | comentario | salvar | marcar"
}}

HASHTAGS SUGERIDAS (escolha 8-12):
Nicho: educacao, ensinosuperior, ead, faculdade, gestaoescolar
Problema: captacaodealunos, matriculas, comercialeducacional
Solução: iaeducacao, automacao, atendimentointeligente
Geral: edtech, inovacaonaeducacao, tecnologiaeducacional

Responda SOMENTE o JSON.
"""
        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini não retornou dict JSON para legenda.")
        return parsed

    # ============================================================
    # VISUAL COPY (TEXTO DO POST)
    # ============================================================
    def generate_visual_copy(self, topic: str) -> dict[str, Any]:
        """
        Gera os textos que aparecem NA IMAGEM do post.
        
        Args:
            topic: Tópico do post
            
        Returns:
            Dict com: headline, subheadline, pexels_query, mood
        """
        prompt = f"""
{SYSTEM_CONTEXT}

## SUA MISSÃO
Crie os TEXTOS que vão aparecer NA IMAGEM do post sobre: {topic}

## HEADLINE (texto principal):
- TUDO EM CAIXA ALTA
- 3 a 6 palavras total
- Dividido em 2-4 linhas (use \\n para quebrar)
- Deve funcionar mesmo sem contexto

Exemplos bons:
- "LEAD\\nÀS 23H?\\nRESPONDA\\nEM 2 MIN"
- "SUA META\\nDE MATRÍCULAS\\nEM RISCO?"
- "+340%\\nMAIS\\nMATRÍCULAS"

## SUBHEADLINE (texto de apoio):
- Frase única, máximo 12 palavras
- Complementa a headline
- SEM ponto final

## PEXELS_QUERY:
- Termo em INGLÊS para buscar foto
- Sempre inclua: pessoa + contexto profissional/educacional
- Adicione "copy space left" para área de texto

Exemplos: 
- "university student laptop campus copy space left"
- "business woman headset customer service"

## FORMATO (JSON):
{{
  "headline": "TEXTO\\nEM\\nLINHAS",
  "subheadline": "Frase de apoio sem ponto final",
  "pexels_query": "specific context person copy space left",
  "mood": "confiança | urgência | resultado | problema"
}}

Responda SOMENTE o JSON.
"""
        raw = self._generate_text(prompt, temperature=0.8)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini não retornou dict JSON para visual copy.")
        return parsed

    # ============================================================
    # BULLETS PARA CARROSSEL
    # ============================================================
    def generate_bullets(self, topic: str, count: int = 4) -> list[str]:
        """
        Gera bullets/pontos-chave para slides de carrossel.
        
        Args:
            topic: Tópico do carrossel
            count: Quantidade de bullets
            
        Returns:
            Lista de strings com os bullets
        """
        prompt = f"""
{SYSTEM_CONTEXT}

## SUA MISSÃO
Gere {count} pontos-chave (bullets) sobre: {topic}

REGRAS:
- Cada bullet deve ter 1 frase curta e impactante
- Máximo 15 palavras por bullet
- Foque em benefícios e resultados, não features
- Use números quando possível
- Evite jargões técnicos

## FORMATO (JSON array de strings):
["Ponto 1", "Ponto 2", "Ponto 3", "Ponto 4"]

Responda SOMENTE o JSON.
"""
        raw = self._generate_text(prompt)
        parsed = self._safe_json_loads(raw)

        if not isinstance(parsed, list):
            raise RuntimeError("Gemini não retornou lista para bullets.")
        return [str(b) for b in parsed[:count]]

    # ============================================================
    # LEGENDA DE CARROSSEL
    # ============================================================
    def write_carousel_caption(
        self,
        topic: str,
        hook: str = "",
        bullets: Optional[list[str]] = None,
    ) -> str:
        """
        Gera legenda otimizada para carrossel do Instagram.
        
        Args:
            topic: Tópico do carrossel
            hook: Gancho/abertura (opcional)
            bullets: Lista de pontos do carrossel (opcional)
            
        Returns:
            String com a legenda completa
        """
        bullets_text = ""
        if bullets:
            bullets_text = "\n".join([f"• {b}" for b in bullets])

        prompt = f"""
{SYSTEM_CONTEXT}

## SUA MISSÃO
Crie uma legenda CURTA para carrossel sobre: {topic}

Hook sugerido: {hook or "(crie um)"}
Pontos do carrossel:
{bullets_text or "(não informados)"}

## REGRAS:
- Máximo 3 parágrafos curtos
- Comece com gancho forte
- Mencione "desliza" ou "arrasta" para ver os slides
- CTA: salvar o post ou comentar
- 5 a 8 hashtags no final

## FORMATO:
Responda APENAS a legenda pronta (texto puro, não JSON).
Separe parágrafos com linha em branco.
Hashtags na última linha.
"""
        caption = self._generate_text(prompt)
        return caption.strip()

    # ============================================================
    # HELPER: PARSE JSON
    # ============================================================
    def _safe_json_loads(self, raw: str) -> Any:
        """Parse JSON com limpeza de formatação comum do Gemini."""
        cleaned = raw.strip()

        # Remove code fences
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        # Encontra o JSON
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
            logger.error("Falha ao parsear JSON. Raw:\n%s", raw[:500])
            raise RuntimeError(f"Gemini retornou JSON inválido: {exc}") from exc