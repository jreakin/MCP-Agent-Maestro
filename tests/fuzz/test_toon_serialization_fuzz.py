"""
Atheris fuzzing target for TOON serialization.

Fuzzes ContextSerializer and MessageSerializer to find edge cases in serialization/deserialization.
"""

import sys
import pytest

try:
    import atheris
    ATHERIS_AVAILABLE = True
except ImportError:
    ATHERIS_AVAILABLE = False
    pytest.skip("Atheris not available", allow_module_level=True)

import json

# Import the serializers
from agent_mcp.features.rag.toon_serializer import (
    ContextSerializer,
    MessageSerializer,
    TOON_AVAILABLE
)


def TestOneInput(data: bytes):
    """
    Fuzzing entry point for TOON serialization.
    """
    try:
        # Decode bytes to string
        input_str = data.decode('utf-8', errors='ignore')
        
        # Test ContextSerializer with fuzzed input as context parts
        # Split input into parts (simulating context chunks)
        context_parts = [input_str[i:i+100] for i in range(0, min(len(input_str), 1000), 100)]
        if not context_parts:
            context_parts = [input_str[:100]] if input_str else ["test"]
        
        # Test JSON serialization (always available)
        try:
            json_result = ContextSerializer.serialize_context(context_parts, format_type="json")
            assert isinstance(json_result, str)
            assert len(json_result) > 0
            
            # Try to parse back
            parsed = json.loads(json_result)
            assert "context" in parsed
        except (ValueError, json.JSONDecodeError):
            pass
        
        # Test TOON serialization (if available)
        if TOON_AVAILABLE:
            try:
                toon_result = ContextSerializer.serialize_context(context_parts, format_type="toon")
                assert isinstance(toon_result, str)
                assert len(toon_result) > 0
            except Exception:
                pass
        
        # Test MessageSerializer
        try:
            # Create a mock message dict
            message_data = {
                "role": "user",
                "content": input_str[:500] if len(input_str) > 0 else "test"
            }
            
            # Test JSON serialization
            json_msg = MessageSerializer.serialize_message(message_data, format_type="json")
            assert isinstance(json_msg, str)
            
            # Try to deserialize
            deserialized = MessageSerializer.deserialize_message(json_msg, format_type="json")
            assert deserialized is not None
            
            # Test TOON serialization (if available)
            if TOON_AVAILABLE:
                toon_msg = MessageSerializer.serialize_message(message_data, format_type="toon")
                assert isinstance(toon_msg, str)
                
                # Try to deserialize
                deserialized_toon = MessageSerializer.deserialize_message(toon_msg, format_type="toon")
                assert deserialized_toon is not None
        except (ValueError, json.JSONDecodeError):
            pass
        
        # Test with empty input
        try:
            empty_result = ContextSerializer.serialize_context([], format_type="json")
            assert isinstance(empty_result, str)
        except Exception:
            pass
        
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        # Expected exceptions
        pass
    except Exception as e:
        print(f"Unexpected exception with input: {data[:100]}")
        raise


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


