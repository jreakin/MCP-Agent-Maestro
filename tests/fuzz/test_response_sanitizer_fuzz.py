"""
Atheris fuzzing target for ResponseSanitizer.

Fuzzes ResponseSanitizer.sanitize() to find edge cases in threat removal/neutralization.
"""

import sys
import pytest

try:
    import atheris
    ATHERIS_AVAILABLE = True
except ImportError:
    ATHERIS_AVAILABLE = False
    pytest.skip("Atheris not available", allow_module_level=True)

# Import the sanitizer and models
from agent_mcp.security.sanitizer import ResponseSanitizer
from agent_mcp.security.models import Threat, ScanResult


def TestOneInput(data: bytes):
    """
    Fuzzing entry point for ResponseSanitizer.sanitize().
    """
    try:
        # Decode bytes to string (may fail, that's okay)
        content = data.decode('utf-8', errors='ignore')
        
        # Create a mock threat for testing
        # Use parts of the fuzzed input as threat content
        threat_content = content[:50] if len(content) > 0 else "test"
        
        threat = Threat(
            type="FUZZ_TEST",
            severity="HIGH",
            content=threat_content,
            pattern_matched=threat_content[:20] if len(threat_content) > 20 else threat_content
        )
        
        scan_result = ScanResult(
            threats=[threat],
            safe=False
        )
        
        # Test all sanitization modes
        for mode in ["remove", "neutralize", "block"]:
            sanitizer = ResponseSanitizer(mode=mode)
            result = sanitizer.sanitize(content, scan_result)
            
            # Basic sanity check: result should be a string
            assert isinstance(result, str)
            
            # In block mode, result should be the blocked message
            if mode == "block":
                assert "[BLOCKED" in result or result == content
        
        # Test with safe content (no threats)
        safe_scan = ScanResult(threats=[], safe=True)
        sanitizer = ResponseSanitizer()
        result = sanitizer.sanitize(content, safe_scan)
        assert result == content  # Safe content should be unchanged
        
    except (ValueError, UnicodeDecodeError):
        # Expected exceptions
        pass
    except Exception as e:
        print(f"Unexpected exception with input: {data[:100]}")
        raise


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


