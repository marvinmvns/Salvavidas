"""LLM service implementations."""
from .openai_service import OpenAILLMService

# LocalLLMService requires llama-cpp-python which may not be installed
try:
    from .local_service import LocalLLMService
    _HAS_LOCAL_LLM = True
except ImportError:
    LocalLLMService = None
    _HAS_LOCAL_LLM = False
    import warnings
    warnings.warn("llama-cpp-python not installed. Local LLM service will be disabled.")

__all__ = ["OpenAILLMService", "LocalLLMService", "_HAS_LOCAL_LLM"]
