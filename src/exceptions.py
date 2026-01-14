# src/exceptions.py
"""Exceções customizadas do EduFlow Automator"""

from __future__ import annotations


class EduFlowError(Exception):
    """Exceção base para todos os erros do EduFlow"""
    pass


class ContentDuplicateError(EduFlowError):
    """Conteúdo duplicado detectado no banco de dados"""
    pass


class APIError(EduFlowError):
    """Erro genérico em chamadas de API"""
    pass


class GeminiAPIError(APIError):
    """Erro específico da API do Gemini"""
    pass


class PexelsAPIError(APIError):
    """Erro específico da API do Pexels"""
    pass


class InstagramAPIError(APIError):
    """Erro específico da API do Instagram"""
    pass


class ConfigurationError(EduFlowError):
    """Erro de configuração (API keys, paths, etc)"""
    pass


class AssetNotFoundError(EduFlowError):
    """Arquivo de asset (logo, fonte, etc) não encontrado"""
    pass