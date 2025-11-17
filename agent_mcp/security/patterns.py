# Agent-MCP Security Patterns
"""
Pattern definitions for detecting prompt injection and context poisoning.
"""

import re
from typing import List, Tuple, Optional


class PatternBasedDetector:
    """
    Detect known prompt injection patterns using regex and heuristics.
    """
    
    # Instruction override patterns
    INJECTION_PATTERNS: List[Tuple[str, str]] = [
        # Instruction overrides
        (r'ignore (previous|above|prior) (instructions|prompts|context)', 'INSTRUCTION_OVERRIDE'),
        (r'disregard (previous|above) (instructions|prompts)', 'INSTRUCTION_OVERRIDE'),
        (r'forget (everything|all) (before|above)', 'INSTRUCTION_OVERRIDE'),
        (r'ignore (all|everything) (above|before|prior)', 'INSTRUCTION_OVERRIDE'),
        
        # Role manipulation
        (r'you are now (a|an) .* instead', 'ROLE_MANIPULATION'),
        (r'act as (a|an) .*', 'ROLE_MANIPULATION'),
        (r'pretend to be .*', 'ROLE_MANIPULATION'),
        (r'you are (a|an) .* now', 'ROLE_MANIPULATION'),
        
        # System prompt leakage attempts
        (r'reveal your (system prompt|instructions)', 'PROMPT_LEAKAGE'),
        (r'what (are|were) your (original|initial) instructions', 'PROMPT_LEAKAGE'),
        (r'show me your (system|initial) prompt', 'PROMPT_LEAKAGE'),
        (r'print your (system|initial) instructions', 'PROMPT_LEAKAGE'),
        
        # Data exfiltration
        (r'send .* to (http|https):\/\/', 'DATA_EXFILTRATION'),
        (r'post .* to .*', 'DATA_EXFILTRATION'),
        (r'upload .* to .*', 'DATA_EXFILTRATION'),
        (r'read .*\.(ssh|env|key|pem)', 'DATA_EXFILTRATION'),
        (r'read .*\.(config|secret|password)', 'DATA_EXFILTRATION'),
        
        # Command injection
        (r'execute (command|script|code)', 'COMMAND_INJECTION'),
        (r'run (bash|sh|python|node) .*', 'COMMAND_INJECTION'),
        (r'eval\(', 'COMMAND_INJECTION'),
        (r'exec\(', 'COMMAND_INJECTION'),
        (r'subprocess\.', 'COMMAND_INJECTION'),
        
        # Context manipulation
        (r'add to context:', 'CONTEXT_MANIPULATION'),
        (r'remember (this|that):', 'CONTEXT_MANIPULATION'),
        (r'important note:', 'CONTEXT_MANIPULATION'),
        (r'store (this|that) in memory', 'CONTEXT_MANIPULATION'),
        
        # Hidden instructions (unicode, whitespace, etc)
        (r'[\u200B-\u200D\uFEFF]', 'HIDDEN_CHARACTERS'),  # Zero-width characters
        
        # Malicious URL patterns
        (r'(api\.)?.*\.(ru|cn|tk)\/exfil', 'SUSPICIOUS_URL'),
        (r'http[s]?://.*\.(ru|cn|tk)/.*', 'SUSPICIOUS_URL'),
    ]
    
    def contains_injection(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if text contains known injection patterns.
        
        Returns:
            Tuple of (is_malicious, threat_type, matched_pattern)
        """
        if not text:
            return False, None, None
            
        text_lower = text.lower()
        
        for pattern, threat_type in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, threat_type, pattern
                
        # Additional structural checks
        if self._has_suspicious_structure(text):
            return True, 'SUSPICIOUS_STRUCTURE', None
            
        return False, None, None
    
    def _has_suspicious_structure(self, text: str) -> bool:
        """
        Detect suspicious structural patterns.
        """
        # Multiple "ignore" statements
        ignore_count = text.lower().count('ignore')
        if ignore_count > 2:
            return True
            
        # Excessive capitalization (shouting instructions)
        if len(text) > 20:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.5:
                return True
                
        # Hidden text patterns (white on white, tiny font, etc)
        if '<span style="color:white">' in text.lower():
            return True
        if '<span style="font-size:0px">' in text.lower():
            return True
        if '<span style="opacity:0">' in text.lower():
            return True
            
        # Excessive use of special characters (potential obfuscation)
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_char_ratio > 0.3 and len(text) > 50:
            return True
            
        return False

