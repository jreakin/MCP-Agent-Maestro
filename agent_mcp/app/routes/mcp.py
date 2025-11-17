"""MCP Setup API routes."""
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...core.config import logger
from ...utils.json_utils import get_sanitized_json_body
from .base import handle_options


async def mcp_config_api_route(request: Request) -> JSONResponse:
    """Generate MCP configuration for a client."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'POST':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    try:
        from ...api.mcp_setup import MCPConfigGenerator
        
        data = await get_sanitized_json_body(request)
        client = data.get('client', 'cursor')
        host = data.get('host', 'localhost')
        port = data.get('port', 8080)
        command = data.get('command', 'agent-mcp')
        
        if client not in ['cursor', 'claude', 'windsurf', 'vscode']:
            return JSONResponse({"error": f"Unsupported client: {client}"}, status_code=400)
        
        generator = MCPConfigGenerator(host=host, port=port, command=command)
        config = generator.generate_config(client)
        
        return JSONResponse({
            "success": True,
            "client": client,
            "config": config
        })
    except Exception as e:
        logger.error(f"Error generating MCP config: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to generate config: {str(e)}"}, status_code=500)


async def mcp_install_api_route(request: Request) -> JSONResponse:
    """Install MCP configuration to a client."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'POST':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    try:
        from ...api.mcp_setup import MCPConfigGenerator, MCPConfigInstaller
        
        data = await get_sanitized_json_body(request)
        client = data.get('client')
        host = data.get('host', 'localhost')
        port = data.get('port', 8080)
        command = data.get('command', 'agent-mcp')
        backup = data.get('backup', True)
        
        if not client or client not in ['cursor', 'claude', 'windsurf', 'vscode']:
            return JSONResponse({"error": f"Unsupported or missing client: {client}"}, status_code=400)
        
        generator = MCPConfigGenerator(host=host, port=port, command=command)
        installer = MCPConfigInstaller()
        
        config = generator.generate_config(client)
        result = installer.install(client, config, backup=backup)
        
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error installing MCP config: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to install config: {str(e)}"}, status_code=500)


async def mcp_verify_all_api_route(request: Request) -> JSONResponse:
    """Verify all MCP client configurations."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'GET':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    try:
        from ...api.mcp_setup import MCPConfigVerifier
        
        verifier = MCPConfigVerifier()
        results = verifier.verify_all()
        
        return JSONResponse({
            "success": True,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error verifying MCP configs: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to verify configs: {str(e)}"}, status_code=500)


# Route definitions
routes = [
    Route('/api/mcp/config', endpoint=mcp_config_api_route, name="mcp_config_api", methods=['POST', 'OPTIONS']),
    Route('/api/mcp/install', endpoint=mcp_install_api_route, name="mcp_install_api", methods=['POST', 'OPTIONS']),
    Route('/api/mcp/verify-all', endpoint=mcp_verify_all_api_route, name="mcp_verify_all_api", methods=['GET', 'OPTIONS']),
]

