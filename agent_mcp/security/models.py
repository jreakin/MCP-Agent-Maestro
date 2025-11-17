# Agent-MCP Security Models
"""
Pydantic models for security threat detection and monitoring.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class Threat(BaseModel):
    """Represents a detected security threat."""
    
    type: str = Field(..., description="Type of threat (e.g., TOOL_DESCRIPTION_POISON)")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ..., description="Severity level of the threat"
    )
    location: Optional[str] = Field(
        None, description="Location where threat was detected (e.g., 'tool.description')"
    )
    content: Optional[str] = Field(
        None, description="The content that triggered the threat (may be truncated)"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score (0.0-1.0) for ML-based detection"
    )
    pattern_matched: Optional[str] = Field(
        None, description="The pattern that matched (for pattern-based detection)"
    )


class ScanResult(BaseModel):
    """Result of a security scan."""
    
    threats: List[Threat] = Field(default_factory=list, description="List of detected threats")
    safe: bool = Field(..., description="Whether the content is safe (no threats detected)")
    sanitized: bool = Field(
        default=False, description="Whether the content was sanitized"
    )
    scan_timestamp: datetime = Field(
        default_factory=datetime.now, description="When the scan was performed"
    )


class ToolUsageRecord(BaseModel):
    """Record of tool usage for behavioral analysis."""
    
    agent_id: str = Field(..., description="ID of the agent using the tool")
    tool_name: str = Field(..., description="Name of the tool being used")
    timestamp: datetime = Field(default_factory=datetime.now)
    params_hash: str = Field(..., description="Hash of tool parameters")
    response_size: int = Field(..., description="Size of the response in bytes")


class SecurityAlert(BaseModel):
    """Security alert for anomalous behavior or threats."""
    
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ..., description="Alert severity"
    )
    message: str = Field(..., description="Alert message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional alert details")
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: Optional[str] = Field(None, description="Agent ID if applicable")
    tool_name: Optional[str] = Field(None, description="Tool name if applicable")

