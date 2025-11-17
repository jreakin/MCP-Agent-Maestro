"""Security monitoring API endpoints."""
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...core.config import logger
from ...utils.json_utils import get_sanitized_json_body
from ...utils.error_handlers import (
    ValidationError,
    create_error_response,
    log_error,
    handle_validation_error,
)
from ...api.models import SecurityScanRequest
from ..decorators import api_route
from ..responses import success_response
from .base import handle_options


@api_route()
async def security_alerts_api_route(request: Request) -> JSONResponse:
    """Get recent security alerts."""
    from ...core import globals as g
    from ...security import SecurityMonitor
    
    if not hasattr(g, 'security_monitor'):
        g.security_monitor = SecurityMonitor()
    
    limit = int(request.query_params.get('limit', 50))
    alerts = await g.security_monitor.get_recent_alerts(limit=limit)
    
    return success_response({
        'alerts': [alert.model_dump() for alert in alerts],
        'count': len(alerts)
    })


@api_route()
async def security_scan_history_api_route(request: Request) -> JSONResponse:
    """Get security scan history."""
    return success_response({
        'scans': [],
        'count': 0
    })


async def security_scan_api_route(request: Request) -> JSONResponse:
    """Scan text content for security threats."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'POST':
        return create_error_response(
            ValidationError("Method not allowed. Use POST for this endpoint."),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        
        try:
            scan_request = SecurityScanRequest(**data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", data, str(e)),
                include_traceback=False
            )
        
        from ...security import PoisonDetector
        
        detector = PoisonDetector()
        scan_result = await detector.scan_text(scan_request.text, context=scan_request.context)
        
        return JSONResponse({
            'safe': scan_result.safe,
            'threats': [threat.model_dump() for threat in scan_result.threats],
            'scan_timestamp': scan_result.scan_timestamp.isoformat()
        })
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "security_scan"}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


# Route definitions
routes = [
    Route('/api/security/alerts', endpoint=security_alerts_api_route, name="security_alerts_api", methods=['GET', 'OPTIONS']),
    Route('/api/security/scan-history', endpoint=security_scan_history_api_route, name="security_scan_history_api", methods=['GET', 'OPTIONS']),
    Route('/api/security/scan', endpoint=security_scan_api_route, name="security_scan_api", methods=['POST', 'OPTIONS']),
]

