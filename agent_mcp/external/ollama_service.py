"""
Ollama service for model detection and management.
Automatically detects available Ollama models and selects appropriate ones.
"""
import os
import httpx
from typing import List, Dict, Optional, Set
from functools import lru_cache
import time

from ..core.config import logger


class OllamaModelDetector:
    """Detects and manages available Ollama models."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama model detector.
        
        Args:
            base_url: Ollama base URL (defaults to OLLAMA_BASE_URL env var or localhost)
        """
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", 
            "http://localhost:11434"
        ).rstrip('/')
        self._available_models: Optional[List[Dict]] = None
        self._last_check: float = 0
        self._cache_ttl: float = 300.0  # Cache for 5 minutes
    
    async def list_available_models(self, force_refresh: bool = False) -> List[Dict]:
        """
        List all available Ollama models.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            List of model dictionaries with 'name' and 'modified_at' keys
        """
        # Check cache
        current_time = time.time()
        if (
            not force_refresh 
            and self._available_models is not None 
            and (current_time - self._last_check) < self._cache_ttl
        ):
            return self._available_models
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                models = data.get("models", [])
                self._available_models = models
                self._last_check = current_time
                
                logger.info(f"Detected {len(models)} Ollama models: {[m.get('name', 'unknown') for m in models]}")
                return models
                
        except httpx.RequestError as e:
            logger.warning(f"Could not connect to Ollama at {self.base_url}: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.warning(f"Ollama API error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}", exc_info=True)
            return []
    
    async def get_model_names(self, force_refresh: bool = False) -> Set[str]:
        """
        Get set of available model names.
        
        Args:
            force_refresh: Force refresh cache
            
        Returns:
            Set of model names
        """
        models = await self.list_available_models(force_refresh)
        return {model.get("name", "") for model in models if model.get("name")}
    
    async def find_best_model(
        self,
        preferred_models: List[str],
        model_type: str = "chat",
        force_refresh: bool = False
    ) -> Optional[str]:
        """
        Find the best available model from preferred list.
        
        Args:
            preferred_models: List of preferred model names (in order of preference)
            model_type: Type of model ("chat", "embedding", "code")
            force_refresh: Force refresh cache
            
        Returns:
            Best available model name or None
        """
        available = await self.get_model_names(force_refresh)
        
        if not available:
            logger.warning("No Ollama models available")
            return None
        
        # Try preferred models in order
        for model in preferred_models:
            if model in available:
                logger.debug(f"Selected {model_type} model: {model}")
                return model
        
        # If no preferred model available, try to find similar
        logger.warning(f"None of preferred {model_type} models available: {preferred_models}")
        
        # Fallback: find any model with relevant keywords
        keywords = {
            "chat": ["llama", "mistral", "qwen", "phi"],
            "embedding": ["embed", "nomic", "mxbai"],
            "code": ["code", "codellama", "deepseek"]
        }
        
        relevant_keywords = keywords.get(model_type, [])
        for model_name in available:
            model_lower = model_name.lower()
            if any(keyword in model_lower for keyword in relevant_keywords):
                logger.info(f"Fallback: Selected {model_type} model: {model_name}")
                return model_name
        
        # Last resort: return first available model
        if available:
            first_model = list(available)[0]
            logger.warning(f"Using first available model as fallback: {first_model}")
            return first_model
        
        return None
    
    async def get_chat_model(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get best available chat model.
        
        Args:
            force_refresh: Force refresh cache
            
        Returns:
            Chat model name or None
        """
        preferred = [
            os.getenv("OLLAMA_CHAT_MODEL", "llama3.2"),
            "llama3.2",
            "llama3.1",
            "llama3",
            "mistral",
            "qwen2.5",
            "phi3"
        ]
        return await self.find_best_model(preferred, "chat", force_refresh)
    
    async def get_embedding_model(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get best available embedding model.
        
        Args:
            force_refresh: Force refresh cache
            
        Returns:
            Embedding model name or None
        """
        preferred = [
            os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
            "nomic-embed-text",
            "mxbai-embed-large",
            "all-minilm"
        ]
        return await self.find_best_model(preferred, "embedding", force_refresh)
    
    async def get_code_model(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get best available code model.
        
        Args:
            force_refresh: Force refresh cache
            
        Returns:
            Code model name or None
        """
        preferred = [
            "codellama",
            "deepseek-coder",
            "qwen2.5-coder",
            "llama3.2"  # Fallback to general model
        ]
        return await self.find_best_model(preferred, "code", force_refresh)
    
    async def is_model_available(self, model_name: str, force_refresh: bool = False) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_name: Model name to check
            force_refresh: Force refresh cache
            
        Returns:
            True if model is available
        """
        available = await self.get_model_names(force_refresh)
        return model_name in available


# Global detector instance
_detector: Optional[OllamaModelDetector] = None


def get_ollama_detector() -> OllamaModelDetector:
    """Get or create global Ollama model detector."""
    global _detector
    if _detector is None:
        _detector = OllamaModelDetector()
    return _detector


async def get_available_ollama_models() -> List[Dict]:
    """Get list of available Ollama models."""
    detector = get_ollama_detector()
    return await detector.list_available_models()


async def get_best_chat_model() -> Optional[str]:
    """Get best available chat model."""
    detector = get_ollama_detector()
    return await detector.get_chat_model()


async def get_best_embedding_model() -> Optional[str]:
    """Get best available embedding model."""
    detector = get_ollama_detector()
    return await detector.get_embedding_model()


async def get_best_code_model() -> Optional[str]:
    """Get best available code model."""
    detector = get_ollama_detector()
    return await detector.get_code_model()
