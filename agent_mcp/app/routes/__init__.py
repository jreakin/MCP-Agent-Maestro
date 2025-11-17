"""Routes package - aggregates all route modules."""
from starlette.routing import Route

# Import health and docs routes
from ..health import health_check_route, metrics_route, readiness_route, liveness_route
from ..openapi import openapi_json_route, swagger_ui_route

# Import prompt routes
from ...api.prompts import (
    list_prompts_api_route,
    get_prompt_api_route,
    create_prompt_api_route,
    update_prompt_api_route,
    delete_prompt_api_route,
    execute_prompt_api_route,
    get_prompt_analytics_api_route,
    export_prompts_api_route,
    import_prompts_api_route,
)

# Import route modules
from .base import handle_options
from .dashboard import routes as dashboard_routes
from .memory import routes as memory_routes
from .security import routes as security_routes
from .tasks import routes as task_routes
from .mcp import routes as mcp_routes
from .websocket import routes as websocket_routes
from .config import routes as config_routes

# Aggregate all routes
routes = [
    # Health and metrics endpoints
    Route('/health', endpoint=health_check_route, name="health_check", methods=['GET']),
    Route('/health/ready', endpoint=readiness_route, name="readiness", methods=['GET']),
    Route('/health/live', endpoint=liveness_route, name="liveness", methods=['GET']),
    Route('/metrics', endpoint=metrics_route, name="metrics", methods=['GET']),
    
    # API Documentation
    Route('/docs', endpoint=swagger_ui_route, name="swagger_ui", methods=['GET']),
    Route('/docs/openapi.json', endpoint=openapi_json_route, name="openapi_json", methods=['GET']),
    
    # Catch-all OPTIONS handler for any API route
    Route('/api/{path:path}', endpoint=handle_options, methods=['OPTIONS']),
]

# Extend with module routes
routes.extend(dashboard_routes)
routes.extend(memory_routes)
routes.extend(security_routes)
routes.extend(task_routes)
routes.extend(mcp_routes)
routes.extend(config_routes)

# Add prompt routes
routes.extend([
    Route('/api/prompts', endpoint=list_prompts_api_route, name="list_prompts_api", methods=['GET', 'OPTIONS']),
    Route('/api/prompts', endpoint=create_prompt_api_route, name="create_prompt_api", methods=['POST', 'OPTIONS']),
    Route('/api/prompts/{prompt_id}', endpoint=get_prompt_api_route, name="get_prompt_api", methods=['GET', 'OPTIONS']),
    Route('/api/prompts/{prompt_id}', endpoint=update_prompt_api_route, name="update_prompt_api", methods=['PUT', 'OPTIONS']),
    Route('/api/prompts/{prompt_id}', endpoint=delete_prompt_api_route, name="delete_prompt_api", methods=['DELETE', 'OPTIONS']),
    Route('/api/prompts/{prompt_id}/execute', endpoint=execute_prompt_api_route, name="execute_prompt_api", methods=['POST', 'OPTIONS']),
    Route('/api/prompts/{prompt_id}/analytics', endpoint=get_prompt_analytics_api_route, name="get_prompt_analytics_api", methods=['GET', 'OPTIONS']),
    Route('/api/prompts/export', endpoint=export_prompts_api_route, name="export_prompts_api", methods=['GET', 'OPTIONS']),
    Route('/api/prompts/import', endpoint=import_prompts_api_route, name="import_prompts_api", methods=['POST', 'OPTIONS']),
])

# Add WebSocket routes
routes.extend(websocket_routes)

