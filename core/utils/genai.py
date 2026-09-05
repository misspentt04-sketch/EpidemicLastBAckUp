# Заглушка для genai (AI отключён)
import logging
logger = logging.getLogger(__name__)

def gpt_thinks(*args, **kwargs):
    """Заглушка вместо реального AI"""
    logger.warning("GPT thinks called but AI is disabled")
    return "AI функция временно отключена"
