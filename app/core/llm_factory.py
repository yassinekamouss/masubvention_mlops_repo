import logging
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Optional LLM imports with graceful degradation
try:
    from langchain_deepseek import ChatDeepSeek
except ImportError:
    ChatDeepSeek = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


class LLMFactory:
    """Factory for initializing LangChain LLM instances based on environment configuration."""

    @classmethod
    def get_llm(cls) -> Optional[Any]:
        """Returns a configured ChatDeepSeek or ChatOpenAI instance, or None if unavailable."""
        if settings.DEEPSEEK_API_KEY and ChatDeepSeek:
            try:
                return ChatDeepSeek(
                    model=settings.DEEPSEEK_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    api_key=settings.DEEPSEEK_API_KEY,
                )
            except Exception as e:
                logger.warning(f"[LLM Setup] Erreur init ChatDeepSeek: {e}")

        if settings.OPENAI_API_KEY and ChatOpenAI:
            try:
                return ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    api_key=settings.OPENAI_API_KEY,
                )
            except Exception as e:
                logger.warning(f"[LLM Setup] Erreur init ChatOpenAI: {e}")

        return None
