# Agent-MCP RAG Intent Classifier
"""
Classify query intent for context-aware RAG responses.
"""

import re
from typing import Optional
from .context import AgentQueryContext


class QueryIntentClassifier:
    """Classify query intent using pattern matching and heuristics."""
    
    # Intent patterns
    IMPLEMENTATION_PATTERNS = [
        r'how (to|do I|can I) (implement|create|build|write|make)',
        r'implement(ation)? (of|for)',
        r'create (a|an)',
        r'build (a|an)',
        r'write (a|an)',
        r'add (a|an)',
    ]
    
    DEBUGGING_PATTERNS = [
        r'why (is|does|isn\'t|doesn\'t)',
        r'error|bug|issue|problem|failing|broken',
        r'fix|debug|troubleshoot',
        r'not working|doesn\'t work',
        r'exception|traceback',
    ]
    
    ARCHITECTURE_PATTERNS = [
        r'architecture|design|structure',
        r'how (does|is) (the|this) (system|application|code) (work|structured)',
        r'explain (the|this) (system|architecture|design)',
        r'data flow|workflow|process',
    ]
    
    SECURITY_PATTERNS = [
        r'security|vulnerability|exploit|attack',
        r'safe|secure|protected',
        r'authentication|authorization|auth',
        r'encryption|hash|password',
        r'sql injection|xss|csrf',
    ]
    
    PLANNING_PATTERNS = [
        r'plan|strategy|approach|steps',
        r'what (should|needs to|must) (I|we) (do|implement)',
        r'break down|decompose|organize',
        r'task breakdown|work breakdown',
    ]
    
    def classify(self, query: str, agent_context: Optional[AgentQueryContext] = None) -> str:
        """
        Classify query intent.
        
        Args:
            query: The query text
            agent_context: Optional agent context
            
        Returns:
            Intent string: 'implementation', 'debugging', 'architecture', 'security', 'planning', or 'general'
        """
        query_lower = query.lower()
        
        # Check patterns in order of specificity
        if self._matches_patterns(query_lower, self.SECURITY_PATTERNS):
            return 'security'
        elif self._matches_patterns(query_lower, self.DEBUGGING_PATTERNS):
            return 'debugging'
        elif self._matches_patterns(query_lower, self.IMPLEMENTATION_PATTERNS):
            return 'implementation'
        elif self._matches_patterns(query_lower, self.ARCHITECTURE_PATTERNS):
            return 'architecture'
        elif self._matches_patterns(query_lower, self.PLANNING_PATTERNS):
            return 'planning'
        
        # Use agent context as hint
        if agent_context:
            if agent_context.agent_role == 'security':
                return 'security'
            elif agent_context.agent_role == 'research':
                return 'architecture'
            elif agent_context.current_task and ('debug' in agent_context.current_task or 'fix' in agent_context.current_task):
                return 'debugging'
        
        return 'general'
    
    def _matches_patterns(self, text: str, patterns: list) -> bool:
        """Check if text matches any of the patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

