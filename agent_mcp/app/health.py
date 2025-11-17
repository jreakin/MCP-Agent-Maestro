"""
Health check and metrics endpoints for monitoring and observability.
"""
from typing import Dict, Any
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
import os

from ..core.config import logger
from ..core.settings import get_settings
from ..db import check_pool_health, get_pool_stats, is_vss_loadable
from ..core import globals as g
from ..db.actions.agent_db import get_all_active_agents_from_db

# psutil is optional for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system metrics will be limited")


async def health_check_route(request: Request) -> JSONResponse:
    """
    Comprehensive health check endpoint.
    Returns 200 if the service is healthy, 503 if unhealthy.
    Checks database, server, embedding service, agent capacity, RAG system, and memory.
    """
    try:
        settings = get_settings()
        health_status: Dict[str, Any] = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {}
        }
        
        # Check database connection pool
        db_healthy = check_pool_health()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "pool_stats": get_pool_stats() if db_healthy else None
        }
        
        # Check if server has started
        has_started = hasattr(g, 'server_start_time')
        health_status["checks"]["server"] = {
            "status": "healthy" if has_started else "unhealthy",
            "started": has_started
        }
        
        # Check embedding service status
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        if embedding_provider == "openai":
            embedding_healthy = settings.openai_api_key is not None
            health_status["checks"]["embedding_service"] = {
                "status": "healthy" if embedding_healthy else "unhealthy",
                "provider": "openai",
                "available": embedding_healthy
            }
        else:
            # For Ollama, we can't easily check without making a request
            # Assume healthy if provider is set
            health_status["checks"]["embedding_service"] = {
                "status": "healthy",
                "provider": "ollama",
                "available": True
            }
        
        # Check agent capacity
        try:
            active_agents = get_all_active_agents_from_db()
            active_count = len(active_agents)
            max_workers = settings.max_workers
            agent_capacity_healthy = active_count <= max_workers
            
            health_status["checks"]["agent_capacity"] = {
                "status": "healthy" if agent_capacity_healthy else "warning",
                "active_agents": active_count,
                "max_workers": max_workers,
                "available_slots": max(0, max_workers - active_count)
            }
        except Exception as e:
            logger.warning(f"Failed to check agent capacity: {e}")
            health_status["checks"]["agent_capacity"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Check RAG system health
        try:
            vss_available = is_vss_loadable()
            rag_enabled = settings.rag_enabled
            
            # Try to check if rag_embeddings table exists
            from ..db import get_db_connection
            conn = None
            rag_table_exists = False
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'rag_embeddings') as exists"
                )
                result = cursor.fetchone()
                rag_table_exists = result['exists'] if isinstance(result, dict) else result[0]
            except Exception:
                pass
            finally:
                if conn:
                    from ..db.postgres_connection import return_connection
                    return_connection(conn)
            
            rag_healthy = rag_enabled and vss_available and rag_table_exists
            
            health_status["checks"]["rag_system"] = {
                "status": "healthy" if rag_healthy else "unhealthy",
                "enabled": rag_enabled,
                "vector_search_available": vss_available,
                "table_exists": rag_table_exists
            }
        except Exception as e:
            logger.warning(f"Failed to check RAG system: {e}")
            health_status["checks"]["rag_system"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Check memory usage
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_percent = process.memory_percent()
                
                # Consider memory healthy if under 90% of system memory
                memory_healthy = memory_percent < 90
                
                health_status["checks"]["memory"] = {
                    "status": "healthy" if memory_healthy else "warning",
                    "memory_mb": round(memory_mb, 2),
                    "memory_percent": round(memory_percent, 2)
                }
            else:
                health_status["checks"]["memory"] = {
                    "status": "unknown",
                    "note": "psutil not available"
                }
        except Exception as e:
            logger.warning(f"Failed to check memory: {e}")
            health_status["checks"]["memory"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Determine overall health
        critical_checks = [
            db_healthy,
            has_started
        ]
        all_critical_healthy = all(critical_checks)
        
        # Check if any checks have warnings
        has_warnings = any(
            check.get("status") == "warning" 
            for check in health_status["checks"].values()
        )
        
        if all_critical_healthy and not has_warnings:
            health_status["status"] = "healthy"
            status_code = 200
        elif all_critical_healthy and has_warnings:
            health_status["status"] = "degraded"
            status_code = 200  # Still return 200 for degraded
        else:
            health_status["status"] = "unhealthy"
            status_code = 503
        
        return JSONResponse(health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return JSONResponse(
            {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503
        )


async def metrics_route(request: Request) -> JSONResponse:
    """
    Metrics endpoint for Prometheus-style monitoring.
    Returns system and application metrics.
    
    Supports two formats:
    - JSON format (default): Returns structured JSON metrics
    - Prometheus format: Returns Prometheus text format (add ?format=prometheus)
    """
    try:
        # Check if Prometheus format is requested
        format_type = request.query_params.get("format", "json").lower()
        
        if format_type == "prometheus":
            from ..utils.metrics import format_prometheus_metrics
            from starlette.responses import Response
            prometheus_text = format_prometheus_metrics()
            return Response(
                content=prometheus_text,
                media_type="text/plain; version=0.0.4"
            )
        
        # JSON format (default)
        metrics: Dict[str, Any] = {
            "timestamp": time.time(),
            "system": {},
            "database": {},
            "application": {},
            "prometheus": {}
        }
        
        # System metrics
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(os.getpid())
                metrics["system"] = {
                    "cpu_percent": process.cpu_percent(interval=0.1),
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "memory_percent": process.memory_percent(),
                    "num_threads": process.num_threads(),
                    "open_files": len(process.open_files()),
                }
                
                # System-wide metrics
                metrics["system"]["cpu_count"] = psutil.cpu_count()
                metrics["system"]["load_average"] = os.getloadavg() if hasattr(os, 'getloadavg') else None
            except Exception as e:
                logger.warning(f"Failed to collect system metrics: {e}")
                metrics["system"]["error"] = str(e)
        else:
            metrics["system"] = {
                "note": "psutil not available - install psutil for detailed system metrics"
            }
        
        # Database pool metrics
        try:
            pool_stats = get_pool_stats()
            db_healthy = check_pool_health()
            metrics["database"] = {
                "pool_healthy": db_healthy,
                "pool_min_connections": pool_stats.get("minconn", 0),
                "pool_max_connections": pool_stats.get("maxconn", 0),
                "pool_closed": pool_stats.get("closed", True),
            }
        except Exception as e:
            logger.warning(f"Failed to collect database metrics: {e}")
            metrics["database"]["error"] = str(e)
        
        # Application metrics
        try:
            metrics["application"] = {
                "active_agents": len(g.active_agents) if hasattr(g, 'active_agents') else 0,
                "total_tasks": len(g.tasks) if hasattr(g, 'tasks') else 0,
                "server_uptime_seconds": (
                    time.time() - time.mktime(time.strptime(g.server_start_time, "%Y-%m-%dT%H:%M:%S.%f"))
                    if hasattr(g, 'server_start_time') and g.server_start_time else None
                ) if hasattr(g, 'server_start_time') else None,
            }
        except Exception as e:
            logger.warning(f"Failed to collect application metrics: {e}")
            metrics["application"]["error"] = str(e)
        
        # Prometheus-style metrics
        try:
            from ..utils.metrics import get_all_metrics
            metrics["prometheus"] = get_all_metrics()
        except Exception as e:
            logger.warning(f"Failed to collect Prometheus metrics: {e}")
            metrics["prometheus"]["error"] = str(e)
        
        return JSONResponse(metrics)
        
    except Exception as e:
        logger.error(f"Error in metrics endpoint: {e}", exc_info=True)
        return JSONResponse(
            {
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=500
        )


async def readiness_route(request: Request) -> JSONResponse:
    """
    Readiness probe endpoint.
    Checks if the service is ready to accept traffic.
    """
    try:
        # Check critical dependencies
        db_ready = check_pool_health()
        server_ready = hasattr(g, 'server_start_time')
        
        ready = db_ready and server_ready
        
        return JSONResponse(
            {
                "ready": ready,
                "checks": {
                    "database": db_ready,
                    "server": server_ready
                },
                "timestamp": time.time()
            },
            status_code=200 if ready else 503
        )
    except Exception as e:
        logger.error(f"Error in readiness check: {e}", exc_info=True)
        return JSONResponse(
            {
                "ready": False,
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503
        )


async def liveness_route(request: Request) -> JSONResponse:
    """
    Liveness probe endpoint.
    Checks if the service is alive (not crashed).
    """
    return JSONResponse(
        {
            "alive": True,
            "timestamp": time.time()
        },
        status_code=200
    )

