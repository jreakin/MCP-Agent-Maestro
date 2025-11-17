"""
Agent modules for Agent-MCP.

NOTE: PydanticAI agents are optional and require pydantic-ai to be installed.
Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai
"""

# PydanticAI agents are optional - import only if available
try:
    from .assessment_agent import AssessmentAgent, assess_and_route, get_assessment_agent
    from .pydanticai_rag_agent import RAGAgent, RAGResponse
    from .pydanticai_task_agent import TaskAgent, TaskOutput
    from .pydanticai_orchestrator import AgentOrchestrator, orchestrate_workflow
    
    __all__ = [
        "AssessmentAgent",
        "assess_and_route",
        "get_assessment_agent",
        "RAGAgent",
        "RAGResponse",
        "TaskAgent",
        "TaskOutput",
        "AgentOrchestrator",
        "orchestrate_workflow",
    ]
except ImportError:
    # PydanticAI not installed - these agents are not available
    __all__ = []
