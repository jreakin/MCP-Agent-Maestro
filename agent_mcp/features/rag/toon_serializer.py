"""
TOON (Token-Oriented Object Notation) serializer for RAG context.
Provides efficient token-saving serialization for LLM contexts.
"""

from typing import Any, Dict, List, Optional, Union
from ...core.config import logger

# Try to import toon, fallback gracefully if not available
try:
    import toon  # type: ignore
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False
    logger.warning("toon-format library not available. TOON serialization will fall back to JSON.")


class ContextSerializer:
    """Serialize RAG context using TOON format for efficient token usage."""
    
    @staticmethod
    def serialize_context(
        context_parts: List[str],
        format_type: str = "json"
    ) -> str:
        """
        Serialize context parts using specified format.
        
        Args:
            context_parts: List of context strings
            format_type: Format to use ('json' or 'toon')
            
        Returns:
            Serialized context string
        """
        if format_type == "toon":
            return ContextSerializer._serialize_to_toon(context_parts)
        else:
            return ContextSerializer._serialize_to_json(context_parts)
    
    @staticmethod
    def _serialize_to_toon(context_parts: List[str]) -> str:
        """Serialize context to TOON format."""
        if not TOON_AVAILABLE:
            logger.warning("TOON not available, falling back to JSON")
            return ContextSerializer._serialize_to_json(context_parts)
        
        try:
            # Convert context parts to structured data
            structured_data = {
                "context": context_parts,
                "count": len(context_parts)
            }
            
            # Encode to TOON
            toon_encoded = toon.encode(structured_data)
            return toon_encoded
        except Exception as e:
            logger.warning(f"Failed to serialize to TOON, falling back to JSON: {e}")
            return ContextSerializer._serialize_to_json(context_parts)
    
    @staticmethod
    def _serialize_to_json(context_parts: List[str]) -> str:
        """Serialize context to JSON format (fallback)."""
        import json
        structured_data = {
            "context": context_parts,
            "count": len(context_parts)
        }
        return json.dumps(structured_data, indent=2)
    
    @staticmethod
    def serialize_results(
        results: List[Dict[str, Any]],
        format_type: str = "json"
    ) -> str:
        """
        Serialize RAG results using specified format.
        
        Args:
            results: List of result dictionaries
            format_type: Format to use ('json' or 'toon')
            
        Returns:
            Serialized results string
        """
        if format_type == "toon":
            return ContextSerializer._serialize_results_to_toon(results)
        else:
            return ContextSerializer._serialize_results_to_json(results)
    
    @staticmethod
    def _serialize_results_to_toon(results: List[Dict[str, Any]]) -> str:
        """Serialize results to TOON format."""
        if not TOON_AVAILABLE:
            logger.warning("TOON not available, falling back to JSON")
            return ContextSerializer._serialize_results_to_json(results)
        
        try:
            # Convert results to structured data
            structured_data = {
                "results": results,
                "count": len(results)
            }
            
            # Encode to TOON
            toon_encoded = toon.encode(structured_data)
            return toon_encoded
        except Exception as e:
            logger.warning(f"Failed to serialize results to TOON, falling back to JSON: {e}")
            return ContextSerializer._serialize_results_to_json(results)
    
    @staticmethod
    def _serialize_results_to_json(results: List[Dict[str, Any]]) -> str:
        """Serialize results to JSON format (fallback)."""
        import json
        structured_data = {
            "results": results,
            "count": len(results)
        }
        return json.dumps(structured_data, indent=2)


class MessageSerializer:
    """Serialize agent-to-agent messages using TOON format."""
    
    @staticmethod
    def serialize_message(
        message: Dict[str, Any],
        format_type: str = "json"
    ) -> str:
        """
        Serialize a message using specified format.
        
        Args:
            message: Message dictionary with keys like 'sender', 'recipient', 'content', etc.
            format_type: Format to use ('json' or 'toon')
            
        Returns:
            Serialized message string
        """
        if format_type == "toon":
            return MessageSerializer._serialize_to_toon(message)
        else:
            return MessageSerializer._serialize_to_json(message)
    
    @staticmethod
    def _serialize_to_toon(message: Dict[str, Any]) -> str:
        """Serialize message to TOON format."""
        if not TOON_AVAILABLE:
            logger.warning("TOON not available, falling back to JSON")
            return MessageSerializer._serialize_to_json(message)
        
        try:
            # Encode message to TOON
            toon_encoded = toon.encode(message)
            return toon_encoded
        except Exception as e:
            logger.warning(f"Failed to serialize message to TOON, falling back to JSON: {e}")
            return MessageSerializer._serialize_to_json(message)
    
    @staticmethod
    def _serialize_to_json(message: Dict[str, Any]) -> str:
        """Serialize message to JSON format (fallback)."""
        import json
        return json.dumps(message, indent=2)
    
    @staticmethod
    def deserialize_message(
        serialized: str,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Deserialize a message from specified format.
        
        Args:
            serialized: Serialized message string
            format_type: Format to use ('json' or 'toon')
            
        Returns:
            Deserialized message dictionary
        """
        if format_type == "toon":
            return MessageSerializer._deserialize_from_toon(serialized)
        else:
            return MessageSerializer._deserialize_from_json(serialized)
    
    @staticmethod
    def _deserialize_from_toon(serialized: str) -> Dict[str, Any]:
        """Deserialize message from TOON format."""
        if not TOON_AVAILABLE:
            logger.warning("TOON not available, falling back to JSON")
            return MessageSerializer._deserialize_from_json(serialized)
        
        try:
            # Decode from TOON
            message = toon.decode(serialized)
            return message if isinstance(message, dict) else {}
        except Exception as e:
            logger.warning(f"Failed to deserialize from TOON, falling back to JSON: {e}")
            return MessageSerializer._deserialize_from_json(serialized)
    
    @staticmethod
    def _deserialize_from_json(serialized: str) -> Dict[str, Any]:
        """Deserialize message from JSON format (fallback)."""
        import json
        try:
            result = json.loads(serialized)
            # Ensure result is a dict
            if isinstance(result, dict):
                return result
            else:
                return {}
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.error("Failed to deserialize JSON message")
            return {}

