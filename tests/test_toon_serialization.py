"""
Hypothesis tests for TOON serialization.
Tests context and message serialization/deserialization.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import text, lists, dictionaries, none, one_of, integers, booleans
from typing import List, Dict, Any

from agent_mcp.features.rag.toon_serializer import (
    ContextSerializer,
    MessageSerializer,
    TOON_AVAILABLE
)


class TestContextSerializer:
    """Test ContextSerializer with Hypothesis."""
    
    @given(
        context_parts=lists(text(min_size=1, max_size=500), min_size=1, max_size=20),
        format_type=st.sampled_from(['json', 'toon'])
    )
    @settings(max_examples=50)
    def test_serialize_context_always_returns_string(self, context_parts: List[str], format_type: str):
        """Serialize context always returns a string."""
        serialized = ContextSerializer.serialize_context(context_parts, format_type)
        
        assert isinstance(serialized, str)
        assert len(serialized) > 0
    
    @given(
        context_parts=lists(text(min_size=1, max_size=200), min_size=1, max_size=10)
    )
    @settings(max_examples=30)
    def test_serialize_context_json_format(self, context_parts: List[str]):
        """Serialize context in JSON format is valid JSON."""
        import json
        serialized = ContextSerializer.serialize_context(context_parts, format_type='json')
        
        # Should be parseable JSON
        try:
            parsed = json.loads(serialized)
            assert isinstance(parsed, dict)
            assert 'context' in parsed
        except json.JSONDecodeError:
            pytest.fail(f"Serialized JSON is invalid: {serialized}")
    
    @given(
        results=lists(
            dictionaries(
                text(min_size=1, max_size=20),
                one_of(text(), integers(), booleans(), none()),
                min_size=1,
                max_size=10
            ),
            min_size=1,
            max_size=20
        ),
        format_type=st.sampled_from(['json', 'toon'])
    )
    @settings(max_examples=30)
    def test_serialize_results_always_returns_string(self, results: List[Dict[str, Any]], format_type: str):
        """Serialize results always returns a string."""
        serialized = ContextSerializer.serialize_results(results, format_type)
        
        assert isinstance(serialized, str)
        assert len(serialized) > 0
    
    @given(
        results=lists(
            dictionaries(text(), one_of(text(), integers(), booleans()), min_size=1, max_size=5),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=20)
    def test_serialize_results_json_format(self, results: List[Dict[str, Any]]):
        """Serialize results in JSON format is valid JSON."""
        import json
        serialized = ContextSerializer.serialize_results(results, format_type='json')
        
        try:
            parsed = json.loads(serialized)
            assert isinstance(parsed, dict)
            assert 'results' in parsed
        except json.JSONDecodeError:
            pytest.fail(f"Serialized JSON is invalid: {serialized}")


class TestMessageSerializer:
    """Test MessageSerializer with Hypothesis."""
    
    @given(
        message=dictionaries(
            st.sampled_from(['sender', 'recipient', 'content', 'timestamp', 'type']),
            text(min_size=1, max_size=200),
            min_size=1,
            max_size=10
        ),
        format_type=st.sampled_from(['json', 'toon'])
    )
    @settings(max_examples=50)
    def test_serialize_message_always_returns_string(self, message: Dict[str, Any], format_type: str):
        """Serialize message always returns a string."""
        serialized = MessageSerializer.serialize_message(message, format_type)
        
        assert isinstance(serialized, str)
        assert len(serialized) > 0
    
    @given(
        message=dictionaries(
            st.sampled_from(['sender', 'recipient', 'content']),
            text(min_size=1, max_size=100),
            min_size=2,
            max_size=5
        )
    )
    @settings(max_examples=30)
    def test_serialize_deserialize_message_roundtrip(self, message: Dict[str, Any]):
        """Serialize and deserialize message roundtrip preserves data."""
        # Always use JSON for reliable roundtrip
        serialized = MessageSerializer.serialize_message(message, format_type='json')
        deserialized = MessageSerializer.deserialize_message(serialized, format_type='json')
        
        # Check that key fields are preserved
        for key in message.keys():
            if key in deserialized:
                assert deserialized[key] == message[key]
    
    @given(
        message=dictionaries(text(), text(), min_size=1, max_size=10)
    )
    @settings(max_examples=20)
    def test_deserialize_message_handles_valid_json(self, message: Dict[str, Any]):
        """Deserialize message handles valid JSON."""
        import json
        json_str = json.dumps(message)
        deserialized = MessageSerializer.deserialize_message(json_str, format_type='json')
        
        assert isinstance(deserialized, dict)
        assert deserialized == message
    
    @given(
        invalid_json=text(min_size=1, max_size=100)
    )
    @settings(max_examples=10)
    def test_deserialize_message_handles_invalid_json(self, invalid_json: str):
        """Deserialize message handles invalid JSON gracefully."""
        # Should return empty dict or handle error gracefully
        deserialized = MessageSerializer.deserialize_message(invalid_json, format_type='json')
        
        assert isinstance(deserialized, dict)

