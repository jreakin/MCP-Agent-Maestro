# Agent-MCP Response Sanitizer
"""
Remove or neutralize poisoned content from tool responses.
"""

import re
from typing import Optional
from .models import Threat, ScanResult
from ..core.config import logger


class ResponseSanitizer:
    """
    Remove or neutralize poisoned content.
    """
    
    def __init__(self, mode: str = "remove"):
        """
        Initialize sanitizer.
        
        Args:
            mode: Sanitization mode - "remove", "neutralize", or "block"
        """
        self.mode = mode
    
    def sanitize(self, content: str, scan_result: ScanResult) -> str:
        """
        Remove or neutralize detected threats.
        
        Args:
            content: Original content
            scan_result: Scan result containing detected threats
            
        Returns:
            Sanitized content
        """
        if scan_result.safe:
            return content
        
        sanitized = content
        
        for threat in scan_result.threats:
            if threat.severity in ['HIGH', 'CRITICAL']:
                if self.mode == "remove":
                    sanitized = self._remove_threat(sanitized, threat)
                elif self.mode == "neutralize":
                    sanitized = self._neutralize_threat(sanitized, threat)
                elif self.mode == "block":
                    # Return a blocked message instead of content
                    return "[BLOCKED: Potential security threat detected. Content not displayed.]"
            elif threat.severity == 'MEDIUM':
                if self.mode in ["remove", "neutralize"]:
                    sanitized = self._neutralize_threat(sanitized, threat)
        
        # Mark as sanitized
        scan_result.sanitized = True
        
        return sanitized
    
    def _remove_threat(self, content: str, threat: Threat) -> str:
        """Remove malicious content entirely."""
        if threat.content:
            # Remove the exact threat content
            content = content.replace(threat.content, "")
            
            # Also try to remove based on pattern if available
            if threat.pattern_matched:
                try:
                    # Escape regex special characters in the pattern
                    pattern = re.escape(threat.pattern_matched)
                    content = re.sub(pattern, "", content, flags=re.IGNORECASE)
                except Exception as e:
                    logger.warning(f"Failed to remove pattern {threat.pattern_matched}: {e}")
        
        # Replace with safe placeholder
        placeholder = "[REMOVED: Potential security threat detected]"
        if placeholder not in content:
            # Only add placeholder if we actually removed something
            if threat.content and threat.content in content:
                # This shouldn't happen, but handle edge cases
                content = content.replace(threat.content, placeholder)
        
        return content
    
    def _neutralize_threat(self, content: str, threat: Threat) -> str:
        """Neutralize by escaping or commenting out."""
        if threat.content:
            # Escape HTML/XML-like content
            neutralized = f"<!-- Flagged as suspicious: {threat.type} -->"
            
            # Try to replace the threat content
            if threat.content in content:
                content = content.replace(threat.content, neutralized)
            elif threat.pattern_matched:
                try:
                    # Try pattern-based replacement
                    pattern = re.escape(threat.pattern_matched)
                    content = re.sub(
                        pattern,
                        neutralized,
                        content,
                        flags=re.IGNORECASE,
                        count=1  # Only replace first occurrence
                    )
                except Exception as e:
                    logger.warning(f"Failed to neutralize pattern {threat.pattern_matched}: {e}")
        
        return content

