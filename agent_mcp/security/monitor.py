# Agent-MCP Security Monitor
"""
Monitor agent behavior for anomalous activity and security threats.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque
from .models import ToolUsageRecord, SecurityAlert
from ..core.config import logger


class SecurityMonitor:
    """
    Monitor agent behavior for anomalous activity.
    """
    
    def __init__(self):
        self.baseline_behavior: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.alert_webhook: Optional[str] = None
        
        # Configuration thresholds
        self.max_calls_per_minute = 50
        self.max_response_size = 100_000  # 100KB
        self.min_history_for_anomaly = 10
        
    async def track_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        tool_params: dict,
        response: Any
    ):
        """
        Track and analyze tool usage patterns.
        
        Args:
            agent_id: ID of the agent making the call
            tool_name: Name of the tool being called
            tool_params: Parameters passed to the tool
            response: Response from the tool
        """
        import hashlib
        
        # Record usage
        params_hash = hashlib.sha256(str(tool_params).encode()).hexdigest()
        response_size = len(str(response))
        
        usage_record = ToolUsageRecord(
            agent_id=agent_id,
            tool_name=tool_name,
            params_hash=params_hash,
            response_size=response_size
        )
        
        # Add to baseline
        self.baseline_behavior[agent_id].append(usage_record)
        
        # Check for anomalies
        if self._is_anomalous_behavior(usage_record):
            alert = SecurityAlert(
                severity='HIGH',
                message=f'Anomalous tool usage detected for agent {agent_id}',
                details={
                    'tool_name': tool_name,
                    'response_size': response_size,
                    'params_hash': params_hash,
                },
                agent_id=agent_id,
                tool_name=tool_name
            )
            
            await self.alert_queue.put(alert)
            logger.warning(f"Security alert: {alert.message}")
            
            # Send to webhook if configured
            if self.alert_webhook:
                await self._send_webhook_alert(alert)
    
    def _is_anomalous_behavior(self, record: ToolUsageRecord) -> bool:
        """
        Detect unusual patterns in tool usage.
        
        Args:
            record: Tool usage record to check
            
        Returns:
            True if behavior is anomalous
        """
        agent_history = list(self.baseline_behavior[record.agent_id])
        
        if len(agent_history) < self.min_history_for_anomaly:
            # Not enough history to determine anomaly
            return False
        
        # Check for unusual frequency
        now = datetime.now()
        recent_calls = [
            r for r in agent_history
            if (now - r.timestamp).total_seconds() < 60
        ]
        if len(recent_calls) > self.max_calls_per_minute:
            return True
        
        # Check for unusual tools
        common_tools = set(r.tool_name for r in agent_history[:-1])  # Exclude current call
        if record.tool_name not in common_tools and len(agent_history) > self.min_history_for_anomaly:
            # New tool for this agent - could be suspicious
            # Only flag if agent has significant history
            return True
        
        # Check for large responses (potential data exfiltration)
        if record.response_size > self.max_response_size:
            return True
        
        # Check for repeated identical calls (potential attack pattern)
        identical_calls = sum(
            1 for r in recent_calls
            if r.tool_name == record.tool_name and r.params_hash == record.params_hash
        )
        if identical_calls > 10:  # More than 10 identical calls in a minute
            return True
        
        return False
    
    async def _send_webhook_alert(self, alert: SecurityAlert):
        """Send alert to configured webhook."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.alert_webhook,
                    json=alert.model_dump(),
                    timeout=5.0
                )
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def get_recent_alerts(self, limit: int = 10) -> List[SecurityAlert]:
        """Get recent security alerts."""
        alerts = []
        temp_queue = asyncio.Queue()
        
        # Drain the queue
        while not self.alert_queue.empty():
            try:
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=0.1)
                alerts.append(alert)
                await temp_queue.put(alert)
            except asyncio.TimeoutError:
                break
        
        # Put alerts back
        while not temp_queue.empty():
            try:
                alert = await asyncio.wait_for(temp_queue.get(), timeout=0.1)
                await self.alert_queue.put(alert)
            except asyncio.TimeoutError:
                break
        
        # Sort by timestamp and return most recent
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]
    
    def set_alert_webhook(self, webhook_url: str):
        """Configure webhook for alerts."""
        self.alert_webhook = webhook_url
        logger.info(f"Security alert webhook configured: {webhook_url}")

