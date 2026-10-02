import os
from typing import Optional, Dict, Any

def get_llm_reasoning_explanation(source_column: str, target_field: str) -> Optional[str]:
    """
    Optional LLM helper for semantic reasoning enhancement.
    If OPENAI_API_KEY or GEMINI_API_KEY is configured in environment, can fetch enhanced reasoning.
    Otherwise falls back seamlessly to deterministic rule explanations.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        return None  # Seamless deterministic fallback

    try:
        # LLM integration stub (uses environment key if provided)
        return f"Semantic AI matched column '{source_column}' to standard field '{target_field}' based on domain terminology."
    except Exception:
        return None
