"""
Atheris fuzzing target for JSON sanitizer.

Fuzzes sanitize_json_input() function to find edge cases and potential security issues.
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

# Import the function to fuzz
from agent_mcp.utils.json_utils import sanitize_json_input


def TestOneInput(data: bytes):
    """
    Fuzzing entry point for sanitize_json_input.
    
    This function is called repeatedly by Atheris with different inputs.
    """
    try:
        # Try fuzzing with bytes input (common in web requests)
        result = sanitize_json_input(data)
        
        # Basic sanity check: result should be a valid Python object
        # (dict, list, or other JSON-serializable type)
        assert result is not None
        
        # Try to serialize back to JSON to ensure it's valid
        json.dumps(result)
        
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        # These are expected exceptions for invalid input
        # Atheris will learn from these and avoid similar inputs
        pass
    except Exception as e:
        # Unexpected exceptions might indicate bugs
        # Log and re-raise to let Atheris know about the issue
        print(f"Unexpected exception with input: {data[:100]}")
        raise


def TestOneInputString(data: bytes):
    """
    Fuzzing entry point for string input.
    """
    try:
        # Decode bytes to string (may fail, that's okay)
        input_str = data.decode('utf-8', errors='ignore')
        
        # Try fuzzing with string input
        result = sanitize_json_input(input_str)
        
        # Basic sanity check
        assert result is not None
        json.dumps(result)
        
    except (ValueError, json.JSONDecodeError):
        # Expected exceptions
        pass
    except Exception as e:
        print(f"Unexpected exception with string input: {data[:100]}")
        raise


if __name__ == "__main__":
    # Configure Atheris to fuzz TestOneInput
    atheris.Setup(sys.argv, TestOneInput)
    
    # Also fuzz the string variant
    # Note: Atheris will run one fuzzer at a time, so we focus on bytes
    atheris.Fuzz()


