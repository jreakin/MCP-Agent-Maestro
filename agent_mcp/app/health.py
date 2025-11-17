"""
Health check and metrics endpoints for monitoring and observability.
"""
from typing import Dict, Any
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
import os

from ..core.config import logger
from ..db import check_pool_health, get_pool_stats
from ..core import globals as g

# psutil is optional for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system metrics will be limited")


async def health_check_route(request: Request) -> JSONResponse:
    """
    Basic health check endpoint.
    Returns 200 if the service is healthy, 503 if unhealthy.
    """
    try:
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
        
        # Determine overall health
        all_healthy = (
            db_healthy and
            has_started
        )
        
        health_status["status"] = "healthy" if all_healthy else "unhealthy"
        
        status_code = 200 if all_healthy else 503
        
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
    """
    try:
        metrics: Dict[str, Any] = {
            "timestamp": time.time(),
            "system": {},
            "database": {},
            "application": {}
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

