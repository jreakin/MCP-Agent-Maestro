"""
Prometheus metrics collection for MCP Agent Maestro.
Tracks agent lifecycle, task completion, RAG performance, and database metrics.
"""
from typing import Dict, Any
from collections import defaultdict
import time
from threading import Lock

# Thread-safe metrics storage
_metrics_lock = Lock()

# Agent metrics
_agent_created_total = 0
_agent_terminated_total = 0
_agent_creation_times: list[float] = []
_agent_termination_times: list[float] = []

# Task metrics
_task_created_total = 0
_task_completed_total = 0
_task_failed_total = 0
_task_assignment_times: list[float] = []
_task_completion_times: list[float] = []
_task_latency_by_status: Dict[str, list[float]] = defaultdict(list)

# RAG metrics
_rag_queries_total = 0
_rag_query_times: list[float] = []
_rag_query_errors = 0
_rag_results_count: list[int] = []

# Database metrics
_db_connection_acquire_times: list[float] = []
_db_query_times: list[float] = []
_db_pool_errors = 0


def record_agent_created(creation_time_ms: float = None):
    """Record an agent creation event."""
    global _agent_created_total
    with _metrics_lock:
        _agent_created_total += 1
        if creation_time_ms is not None:
            _agent_creation_times.append(creation_time_ms)
            # Keep only last 1000
            if len(_agent_creation_times) > 1000:
                _agent_creation_times.pop(0)


def record_agent_terminated(termination_time_ms: float = None):
    """Record an agent termination event."""
    global _agent_terminated_total
    with _metrics_lock:
        _agent_terminated_total += 1
        if termination_time_ms is not None:
            _agent_termination_times.append(termination_time_ms)
            # Keep only last 1000
            if len(_agent_termination_times) > 1000:
                _agent_termination_times.pop(0)


def record_task_created():
    """Record a task creation event."""
    global _task_created_total
    with _metrics_lock:
        _task_created_total += 1


def record_task_completed(completion_time_ms: float = None, latency_ms: float = None):
    """Record a task completion event."""
    global _task_completed_total
    with _metrics_lock:
        _task_completed_total += 1
        if completion_time_ms is not None:
            _task_completion_times.append(completion_time_ms)
            if len(_task_completion_times) > 1000:
                _task_completion_times.pop(0)
        if latency_ms is not None:
            _task_latency_by_status["completed"].append(latency_ms)
            if len(_task_latency_by_status["completed"]) > 1000:
                _task_latency_by_status["completed"].pop(0)


def record_task_failed():
    """Record a task failure event."""
    global _task_failed_total
    with _metrics_lock:
        _task_failed_total += 1


def record_task_assigned(assignment_time_ms: float = None):
    """Record a task assignment event."""
    global _task_assignment_times
    with _metrics_lock:
        if assignment_time_ms is not None:
            _task_assignment_times.append(assignment_time_ms)
            if len(_task_assignment_times) > 1000:
                _task_assignment_times.pop(0)


def record_rag_query(query_time_ms: float = None, results_count: int = None, error: bool = False):
    """Record a RAG query event."""
    global _rag_queries_total, _rag_query_times, _rag_query_errors, _rag_results_count
    with _metrics_lock:
        _rag_queries_total += 1
        if error:
            _rag_query_errors += 1
        if query_time_ms is not None:
            _rag_query_times.append(query_time_ms)
            if len(_rag_query_times) > 1000:
                _rag_query_times.pop(0)
        if results_count is not None:
            _rag_results_count.append(results_count)
            if len(_rag_results_count) > 1000:
                _rag_results_count.pop(0)


def record_db_connection_acquire(acquire_time_ms: float = None):
    """Record a database connection acquisition."""
    global _db_connection_acquire_times
    with _metrics_lock:
        if acquire_time_ms is not None:
            _db_connection_acquire_times.append(acquire_time_ms)
            if len(_db_connection_acquire_times) > 1000:
                _db_connection_acquire_times.pop(0)


def record_db_query(query_time_ms: float = None):
    """Record a database query."""
    global _db_query_times
    with _metrics_lock:
        if query_time_ms is not None:
            _db_query_times.append(query_time_ms)
            if len(_db_query_times) > 1000:
                _db_query_times.pop(0)


def record_db_pool_error():
    """Record a database pool error."""
    global _db_pool_errors
    with _metrics_lock:
        _db_pool_errors += 1


def get_all_metrics() -> Dict[str, Any]:
    """Get all collected metrics."""
    with _metrics_lock:
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0.0
        
        def p95(lst):
            if not lst:
                return 0.0
            sorted_lst = sorted(lst)
            index = int(len(sorted_lst) * 0.95)
            return sorted_lst[index] if index < len(sorted_lst) else sorted_lst[-1]
        
        return {
            "agents": {
                "created_total": _agent_created_total,
                "terminated_total": _agent_terminated_total,
                "active": _agent_created_total - _agent_terminated_total,
                "creation_time_avg_ms": avg(_agent_creation_times),
                "creation_time_p95_ms": p95(_agent_creation_times),
                "termination_time_avg_ms": avg(_agent_termination_times),
            },
            "tasks": {
                "created_total": _task_created_total,
                "completed_total": _task_completed_total,
                "failed_total": _task_failed_total,
                "completion_rate": (
                    _task_completed_total / _task_created_total 
                    if _task_created_total > 0 else 0.0
                ),
                "assignment_time_avg_ms": avg(_task_assignment_times),
                "assignment_time_p95_ms": p95(_task_assignment_times),
                "completion_time_avg_ms": avg(_task_completion_times),
                "completion_time_p95_ms": p95(_task_completion_times),
                "latency_avg_ms": avg(_task_latency_by_status.get("completed", [])),
            },
            "rag": {
                "queries_total": _rag_queries_total,
                "query_errors": _rag_query_errors,
                "query_error_rate": (
                    _rag_query_errors / _rag_queries_total 
                    if _rag_queries_total > 0 else 0.0
                ),
                "query_time_avg_ms": avg(_rag_query_times),
                "query_time_p95_ms": p95(_rag_query_times),
                "results_avg": avg(_rag_results_count) if _rag_results_count else 0.0,
            },
            "database": {
                "connection_acquire_time_avg_ms": avg(_db_connection_acquire_times),
                "connection_acquire_time_p95_ms": p95(_db_connection_acquire_times),
                "query_time_avg_ms": avg(_db_query_times),
                "query_time_p95_ms": p95(_db_query_times),
                "pool_errors_total": _db_pool_errors,
            }
        }


def format_prometheus_metrics() -> str:
    """Format metrics in Prometheus text format."""
    metrics = get_all_metrics()
    lines = []
    
    # Agent metrics
    lines.append(f"# HELP maestro_agents_created_total Total number of agents created")
    lines.append(f"# TYPE maestro_agents_created_total counter")
    lines.append(f"maestro_agents_created_total {metrics['agents']['created_total']}")
    
    lines.append(f"# HELP maestro_agents_terminated_total Total number of agents terminated")
    lines.append(f"# TYPE maestro_agents_terminated_total counter")
    lines.append(f"maestro_agents_terminated_total {metrics['agents']['terminated_total']}")
    
    lines.append(f"# HELP maestro_agents_active Current number of active agents")
    lines.append(f"# TYPE maestro_agents_active gauge")
    lines.append(f"maestro_agents_active {metrics['agents']['active']}")
    
    lines.append(f"# HELP maestro_agent_creation_time_ms Agent creation time in milliseconds")
    lines.append(f"# TYPE maestro_agent_creation_time_ms histogram")
    lines.append(f"maestro_agent_creation_time_ms_avg {metrics['agents']['creation_time_avg_ms']:.2f}")
    lines.append(f"maestro_agent_creation_time_ms_p95 {metrics['agents']['creation_time_p95_ms']:.2f}")
    
    # Task metrics
    lines.append(f"# HELP maestro_tasks_created_total Total number of tasks created")
    lines.append(f"# TYPE maestro_tasks_created_total counter")
    lines.append(f"maestro_tasks_created_total {metrics['tasks']['created_total']}")
    
    lines.append(f"# HELP maestro_tasks_completed_total Total number of tasks completed")
    lines.append(f"# TYPE maestro_tasks_completed_total counter")
    lines.append(f"maestro_tasks_completed_total {metrics['tasks']['completed_total']}")
    
    lines.append(f"# HELP maestro_tasks_failed_total Total number of tasks failed")
    lines.append(f"# TYPE maestro_tasks_failed_total counter")
    lines.append(f"maestro_tasks_failed_total {metrics['tasks']['failed_total']}")
    
    lines.append(f"# HELP maestro_task_completion_rate Task completion rate (0.0 to 1.0)")
    lines.append(f"# TYPE maestro_task_completion_rate gauge")
    lines.append(f"maestro_task_completion_rate {metrics['tasks']['completion_rate']:.4f}")
    
    lines.append(f"# HELP maestro_task_assignment_time_ms Task assignment time in milliseconds")
    lines.append(f"# TYPE maestro_task_assignment_time_ms histogram")
    lines.append(f"maestro_task_assignment_time_ms_avg {metrics['tasks']['assignment_time_avg_ms']:.2f}")
    lines.append(f"maestro_task_assignment_time_ms_p95 {metrics['tasks']['assignment_time_p95_ms']:.2f}")
    
    lines.append(f"# HELP maestro_task_completion_time_ms Task completion time in milliseconds")
    lines.append(f"# TYPE maestro_task_completion_time_ms histogram")
    lines.append(f"maestro_task_completion_time_ms_avg {metrics['tasks']['completion_time_avg_ms']:.2f}")
    lines.append(f"maestro_task_completion_time_ms_p95 {metrics['tasks']['completion_time_p95_ms']:.2f}")
    
    # RAG metrics
    lines.append(f"# HELP maestro_rag_queries_total Total number of RAG queries")
    lines.append(f"# TYPE maestro_rag_queries_total counter")
    lines.append(f"maestro_rag_queries_total {metrics['rag']['queries_total']}")
    
    lines.append(f"# HELP maestro_rag_query_errors_total Total number of RAG query errors")
    lines.append(f"# TYPE maestro_rag_query_errors_total counter")
    lines.append(f"maestro_rag_query_errors_total {metrics['rag']['query_errors']}")
    
    lines.append(f"# HELP maestro_rag_query_time_ms RAG query time in milliseconds")
    lines.append(f"# TYPE maestro_rag_query_time_ms histogram")
    lines.append(f"maestro_rag_query_time_ms_avg {metrics['rag']['query_time_avg_ms']:.2f}")
    lines.append(f"maestro_rag_query_time_ms_p95 {metrics['rag']['query_time_p95_ms']:.2f}")
    
    lines.append(f"# HELP maestro_rag_results_avg Average number of results per RAG query")
    lines.append(f"# TYPE maestro_rag_results_avg gauge")
    lines.append(f"maestro_rag_results_avg {metrics['rag']['results_avg']:.2f}")
    
    # Database metrics
    lines.append(f"# HELP maestro_db_connection_acquire_time_ms Database connection acquisition time in milliseconds")
    lines.append(f"# TYPE maestro_db_connection_acquire_time_ms histogram")
    lines.append(f"maestro_db_connection_acquire_time_ms_avg {metrics['database']['connection_acquire_time_avg_ms']:.2f}")
    lines.append(f"maestro_db_connection_acquire_time_ms_p95 {metrics['database']['connection_acquire_time_p95_ms']:.2f}")
    
    lines.append(f"# HELP maestro_db_query_time_ms Database query time in milliseconds")
    lines.append(f"# TYPE maestro_db_query_time_ms histogram")
    lines.append(f"maestro_db_query_time_ms_avg {metrics['database']['query_time_avg_ms']:.2f}")
    lines.append(f"maestro_db_query_time_ms_p95 {metrics['database']['query_time_p95_ms']:.2f}")
    
    lines.append(f"# HELP maestro_db_pool_errors_total Total number of database pool errors")
    lines.append(f"# TYPE maestro_db_pool_errors_total counter")
    lines.append(f"maestro_db_pool_errors_total {metrics['database']['pool_errors_total']}")
    
    return "\n".join(lines) + "\n"


def reset_metrics():
    """Reset all metrics (useful for testing)."""
    global _agent_created_total, _agent_terminated_total, _agent_creation_times, _agent_termination_times
    global _task_created_total, _task_completed_total, _task_failed_total
    global _task_assignment_times, _task_completion_times, _task_latency_by_status
    global _rag_queries_total, _rag_query_times, _rag_query_errors, _rag_results_count
    global _db_connection_acquire_times, _db_query_times, _db_pool_errors
    
    with _metrics_lock:
        _agent_created_total = 0
        _agent_terminated_total = 0
        _agent_creation_times.clear()
        _agent_termination_times.clear()
        
        _task_created_total = 0
        _task_completed_total = 0
        _task_failed_total = 0
        _task_assignment_times.clear()
        _task_completion_times.clear()
        _task_latency_by_status.clear()
        
        _rag_queries_total = 0
        _rag_query_times.clear()
        _rag_query_errors = 0
        _rag_results_count.clear()
        
        _db_connection_acquire_times.clear()
        _db_query_times.clear()
        _db_pool_errors = 0

