# Agent-MCP Prompt Book API
"""
Backend API endpoints for prompt book management.
"""

import json
from typing import List, Dict, Any, Optional
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..core.config import logger
from ..core.auth import verify_token, get_agent_id as auth_get_agent_id
from ..prompts.storage import get_prompt_storage
from ..app.decorators import api_route
import mcp.types as mcp_types


async def list_prompts_api_route(request: Request) -> JSONResponse:
    """List all prompts with optional filters."""
    if request.method == 'OPTIONS':
        from ..app.routes import handle_options
        return await handle_options(request)
    
    try:
        category = request.query_params.get('category')
        agent_role = request.query_params.get('agent_role')
        tags = request.query_params.getlist('tags') if hasattr(request.query_params, 'getlist') else []
        
        storage = get_prompt_storage()
        prompts = storage.list_prompts(
            category=category,
            agent_role=agent_role,
            tags=tags if tags else None
        )
        
        return JSONResponse({'prompts': prompts, 'count': len(prompts)})
    except Exception as e:
        logger.error(f"Error in list_prompts_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to list prompts: {str(e)}"}, status_code=500)


async def get_prompt_api_route(request: Request) -> JSONResponse:
    """Get a single prompt by ID."""
    if request.method == 'OPTIONS':
        from ..app.routes import handle_options
        return await handle_options(request)
    
    prompt_id = request.path_params.get('prompt_id')
    if not prompt_id:
        return JSONResponse({"error": "prompt_id is required"}, status_code=400)
    
    try:
        storage = get_prompt_storage()
        prompt = storage.get_prompt(prompt_id)
        if not prompt:
            return JSONResponse({"error": "Prompt not found"}, status_code=404)
        return JSONResponse(prompt)
    except Exception as e:
        logger.error(f"Error in get_prompt_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to get prompt: {str(e)}"}, status_code=500)


async def create_prompt_api_route(request: Request) -> JSONResponse:
    """Create a new prompt template."""
    if request.method == 'OPTIONS':
        from ..app.routes import handle_options
        return await handle_options(request)
    
    if request.method != 'POST':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    try:
        data = await request.json()
        token = data.get('token')
        
        if not verify_token(token, required_role='admin'):
            return JSONResponse({"error": "Invalid admin token"}, status_code=403)
        
        created_by = auth_get_agent_id(token) or 'admin'
        
        storage = get_prompt_storage()
        prompt_id = storage.create_prompt(data, created_by=created_by)
        
        prompt = storage.get_prompt(prompt_id)
        return JSONResponse(prompt, status_code=201)
    except Exception as e:
        logger.error(f"Error in create_prompt_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to create prompt: {str(e)}"}, status_code=500)


async def update_prompt_api_route(request: Request) -> JSONResponse:
    """Update an existing prompt."""
    if request.method == 'OPTIONS':
        from ..app.routes import handle_options
        return await handle_options(request)
    
    if request.method != 'PUT':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    prompt_id = request.path_params.get('prompt_id')
    if not prompt_id:
        return JSONResponse({"error": "prompt_id is required"}, status_code=400)
    
    try:
        data = await request.json()
        token = data.get('token')
        
        if not verify_token(token, required_role='admin'):
            return JSONResponse({"error": "Invalid admin token"}, status_code=403)
        
        # Remove token from updates
        updates = {k: v for k, v in data.items() if k != 'token'}
        
        storage = get_prompt_storage()
        success = storage.update_prompt(prompt_id, updates)
        
        if not success:
            return JSONResponse({"error": "Prompt not found or update failed"}, status_code=404)
        
        prompt = storage.get_prompt(prompt_id)
        return JSONResponse(prompt)
    except Exception as e:
        logger.error(f"Error in update_prompt_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to update prompt: {str(e)}"}, status_code=500)


async def delete_prompt_api_route(request: Request) -> JSONResponse:
    """Delete a prompt."""
    if request.method == 'OPTIONS':
        from ..app.routes import handle_options
        return await handle_options(request)
    
    if request.method != 'DELETE':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    prompt_id = request.path_params.get('prompt_id')
    if not prompt_id:
        return JSONResponse({"error": "prompt_id is required"}, status_code=400)
    
    try:
        data = await request.json()
        token = data.get('token') if request.method == 'DELETE' else None
        
        # For DELETE, token might be in query params or body
        if not token:
            token = request.query_params.get('token')
        
        if not verify_token(token, required_role='admin'):
            return JSONResponse({"error": "Invalid admin token"}, status_code=403)
        
        storage = get_prompt_storage()
        success = storage.delete_prompt(prompt_id)
        
        if not success:
            return JSONResponse({"error": "Prompt not found"}, status_code=404)
        
        return JSONResponse({"success": True, "message": f"Prompt {prompt_id} deleted"})
    except Exception as e:
        logger.error(f"Error in delete_prompt_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to delete prompt: {str(e)}"}, status_code=500)


async def execute_prompt_api_route(request: Request) -> JSONResponse:
    """Execute a prompt with given variables on specified agent."""
    if request.method == 'OPTIONS':
        from ..app.routes import handle_options
        return await handle_options(request)
    
    if request.method != 'POST':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    prompt_id = request.path_params.get('prompt_id')
    if not prompt_id:
        return JSONResponse({"error": "prompt_id is required"}, status_code=400)
    
    try:
        data = await get_sanitized_json_body(request)
        variables = data.get('variables', {})
        agent_id = data.get('agent_id')
        token = data.get('token')
        
        if not verify_token(token, required_role='admin'):
            return JSONResponse({"error": "Invalid admin token"}, status_code=403)
        
        storage = get_prompt_storage()
        prompt = storage.get_prompt(prompt_id)
        
        if not prompt:
            return JSONResponse({"error": "Prompt not found"}, status_code=404)
        
        # Fill template with variables
        template = prompt['template']
        for var_name, var_value in variables.items():
            template = template.replace(f'{{{{{var_name}}}}}', str(var_value))
        
        # Send to agent if specified
        if agent_id:
            # TODO: Integrate with agent communication tools when available
            # For now, just return the filled template
            storage.increment_usage(prompt_id)
            return JSONResponse({
                'success': True,
                'message': 'Prompt prepared for agent',
                'filled_template': template,
                'agent_id': agent_id,
                'note': 'Agent communication integration pending'
            })
        else:
            # Just return filled template
            storage.increment_usage(prompt_id)
            return JSONResponse({
                'success': True,
                'filled_template': template
            })
    except Exception as e:
        logger.error(f"Error in execute_prompt_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to execute prompt: {str(e)}"}, status_code=500)


async def get_prompt_analytics_api_route(request: Request) -> JSONResponse:
    """Get usage statistics and success metrics for a prompt."""
    from ..app.responses import success_response, error_response
    
    prompt_id = request.path_params.get('prompt_id')
    if not prompt_id:
        return error_response("prompt_id is required", status_code=400)
    
    try:
        storage = get_prompt_storage()
        prompt = storage.get_prompt(prompt_id)
        
        if not prompt:
            return error_response("Prompt not found", status_code=404)
        
        return success_response({
            'prompt_id': prompt_id,
            'usage_count': prompt.get('usage_count', 0),
            'success_rate': prompt.get('success_rate', 0.0),
            'created_at': prompt.get('created_at'),
            'updated_at': prompt.get('updated_at')
        })
    except Exception as e:
        logger.error(f"Error in get_prompt_analytics_api_route: {e}", exc_info=True)
        return error_response(f"Failed to get prompt analytics: {str(e)}", status_code=500)

@api_route(require_auth_role="admin")
async def export_prompts_api_route(request: Request, token: str) -> JSONResponse:
    """Export all prompts as JSON."""
    from ..app.responses import success_response
    
    try:
        storage = get_prompt_storage()
        prompts = storage.list_prompts()
        return success_response({"prompts": prompts, "count": len(prompts)})
    except Exception as e:
        logger.error(f"Error in export_prompts_api_route: {e}", exc_info=True)
        return error_response(f"Failed to export prompts: {str(e)}", status_code=500)

@api_route(require_auth_role="admin")
async def import_prompts_api_route(request: Request, token: str) -> JSONResponse:
    """Import prompts from JSON."""
    from ..app.responses import success_response, error_response
    
    try:
        data = await request.json()
        prompts = data.get('prompts', [])
        
        if not isinstance(prompts, list):
            return error_response("Invalid format: 'prompts' must be an array", status_code=400)
        
        storage = get_prompt_storage()
        imported_count = 0
        
        for prompt_data in prompts:
            try:
                # Validate required fields
                if not prompt_data.get('prompt_id') or not prompt_data.get('template'):
                    continue
                
                # Check if prompt exists
                existing = storage.get_prompt(prompt_data['prompt_id'])
                if existing:
                    # Update existing
                    storage.update_prompt(prompt_data['prompt_id'], prompt_data)
                else:
                    # Create new
                    storage.create_prompt(prompt_data, created_by='import')
                imported_count += 1
            except Exception as e:
                logger.warning(f"Failed to import prompt {prompt_data.get('prompt_id', 'unknown')}: {e}")
                continue
        
        return success_response({"imported": imported_count, "total": len(prompts)})
    except Exception as e:
        logger.error(f"Error in import_prompts_api_route: {e}", exc_info=True)
        return error_response(f"Failed to import prompts: {str(e)}", status_code=500)

