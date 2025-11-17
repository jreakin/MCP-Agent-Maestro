# Agent-MCP Poison Detector
"""
Main detection engine for prompt injection and context poisoning.
"""

from typing import Any, Dict, List, Optional
from .models import Threat, ScanResult
from .patterns import PatternBasedDetector
from ..core.config import logger


class PoisonDetector:
    """
    Detect prompt injection and context poisoning attempts.
    """
    
    def __init__(self):
        self.pattern_detector = PatternBasedDetector()
        # ML-based detector can be added later
        self.ml_detector = None
        
    async def scan_tool_schema(self, tool_schema: dict) -> ScanResult:
        """
        Scan MCP tool schema for malicious content.
        Checks: description, parameter descriptions, example values.
        
        Args:
            tool_schema: Dictionary containing tool schema information
            
        Returns:
            ScanResult with detected threats
        """
        threats: List[Threat] = []
        
        # Check tool description
        description = tool_schema.get('description', '')
        if description and isinstance(description, str):
            is_malicious, threat_type, pattern = self.pattern_detector.contains_injection(description)
            if is_malicious:
                threats.append(Threat(
                    type='TOOL_DESCRIPTION_POISON',
                    severity='HIGH',
                    location='tool.description',
                    content=description[:500],  # Truncate for logging
                    pattern_matched=pattern
                ))
        
        # Check parameter descriptions
        parameters = tool_schema.get('parameters', {})
        if not isinstance(parameters, dict):
            parameters = {}
        properties = parameters.get('properties', {}) if isinstance(parameters, dict) else {}
        
        for param_name, param_def in properties.items():
            if not isinstance(param_def, dict):
                continue
            param_description = param_def.get('description', '')
            if param_description:
                is_malicious, threat_type, pattern = self.pattern_detector.contains_injection(param_description)
                if is_malicious:
                    threats.append(Threat(
                        type='PARAMETER_DESCRIPTION_POISON',
                        severity='MEDIUM',
                        location=f'parameter.{param_name}',
                        content=param_description[:500],
                        pattern_matched=pattern
                    ))
            
            # Check example values
            if isinstance(param_def, dict) and 'examples' in param_def:
                examples = param_def['examples']
                if isinstance(examples, list):
                    for i, example in enumerate(examples):
                        example_str = str(example)
                        is_malicious, threat_type, pattern = self.pattern_detector.contains_injection(example_str)
                        if is_malicious:
                            threats.append(Threat(
                                type='PARAMETER_EXAMPLE_POISON',
                                severity='MEDIUM',
                                location=f'parameter.{param_name}.examples[{i}]',
                                content=example_str[:500],
                                pattern_matched=pattern
                            ))
        
        return ScanResult(threats=threats, safe=len(threats) == 0)
    
    async def scan_tool_response(self, response: Any) -> ScanResult:
        """
        Scan tool execution response for injected content.
        
        Args:
            response: The tool response (can be any type, will be converted to string)
            
        Returns:
            ScanResult with detected threats
        """
        threats: List[Threat] = []
        response_str = str(response)
        
        # Pattern-based detection
        is_malicious, threat_type, pattern = self.pattern_detector.contains_injection(response_str)
        if is_malicious:
            threats.append(Threat(
                type='RESPONSE_CONTENT_POISON',
                severity='HIGH',
                content=response_str[:500],  # Truncate for logging
                pattern_matched=pattern
            ))
        
        # ML-based detection (if enabled in future)
        if self.ml_detector and self.ml_detector.enabled:
            try:
                ml_result = await self.ml_detector.classify(response_str)
                if ml_result.is_malicious:
                    threats.append(Threat(
                        type='ML_DETECTED_POISON',
                        severity='HIGH',
                        confidence=ml_result.confidence
                    ))
            except Exception as e:
                logger.warning(f"ML detection failed: {e}")
        
        return ScanResult(threats=threats, safe=len(threats) == 0)
    
    async def scan_text(self, text: str, context: Optional[str] = None) -> ScanResult:
        """
        Scan arbitrary text for injection patterns.
        
        Args:
            text: Text to scan
            context: Optional context about where the text came from
            
        Returns:
            ScanResult with detected threats
        """
        threats: List[Threat] = []
        
        is_malicious, threat_type, pattern = self.pattern_detector.contains_injection(text)
        if is_malicious:
            threats.append(Threat(
                type=threat_type or 'TEXT_POISON',
                severity='HIGH',
                location=context,
                content=text[:500],
                pattern_matched=pattern
            ))
        
        return ScanResult(threats=threats, safe=len(threats) == 0)

