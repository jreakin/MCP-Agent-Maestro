"""Memory CRUD API endpoints."""
import json
import datetime

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...core.config import logger
from ...core.auth import verify_token, get_agent_id as auth_get_agent_id
from ...utils.json_utils import get_sanitized_json_body
from ...utils.error_handlers import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    ConflictError,
    create_error_response,
    log_error,
    handle_validation_error,
)
from ...api.models import MemoryCreate, MemoryUpdate
from ...db import db_connection
from ...db.actions.agent_actions_db import log_agent_action_to_db
from .base import handle_options


async def create_sample_memories_route(request: Request) -> JSONResponse:
    """Create sample memory entries for testing"""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            sample_memories = [
                {
                    'context_key': 'api.config.base_url',
                    'value': json.dumps('https://api.example.com'),
                    'description': 'Main API base URL for external services',
                    'updated_by': 'system'
                },
                {
                    'context_key': 'app.settings.theme',
                    'value': json.dumps({'theme': 'dark', 'accent': 'blue'}),
                    'description': 'Application theme preferences',
                    'updated_by': 'admin'
                },
                {
                    'context_key': 'database.connection.timeout',
                    'value': json.dumps(30),
                    'description': 'Database connection timeout in seconds',
                    'updated_by': 'system'
                },
                {
                    'context_key': 'cache.redis.config',
                    'value': json.dumps({
                        'host': 'localhost',
                        'port': 6379,
                        'ttl': 3600
                    }),
                    'description': 'Redis cache configuration',
                    'updated_by': 'admin'
                }
            ]
            
            created_count = 0
            
            for memory in sample_memories:
                cursor.execute("""
                    INSERT INTO project_context (context_key, value, last_updated, updated_by, description)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)
                    ON CONFLICT (context_key) DO UPDATE SET
                        value = %s,
                        last_updated = CURRENT_TIMESTAMP,
                        updated_by = %s,
                        description = %s
                """, (
                    memory['context_key'],
                    memory['value'],
                    memory['updated_by'],
                    memory['description'],
                    memory['value'],
                    memory['updated_by'],
                    memory['description']
                ))
                created_count += 1
            
            conn.commit()
            
            return JSONResponse({
                "success": True,
                "message": f"Created {created_count} sample memory entries",
                "created_count": created_count
            })
        
    except Exception as e:
        logger.error(f"Error creating sample memories: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


async def create_memory_api_route(request: Request) -> JSONResponse:
    """Create a new memory entry"""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'POST':
        return create_error_response(
            ValidationError("Method not allowed. Use POST for this endpoint."),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        admin_token = data.get('token')
        
        if not verify_token(admin_token, required_role='admin'):
            return create_error_response(
                AuthenticationError("Invalid admin token"),
                include_traceback=False
            )
        
        memory_data = {k: v for k, v in data.items() if k != 'token'}
        try:
            memory_create = MemoryCreate(**memory_data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", memory_data, str(e)),
                include_traceback=False
            )
        
        requesting_admin_id = auth_get_agent_id(admin_token)
        
        with db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT context_key FROM project_context WHERE context_key = %s", (memory_create.context_key,))
            if cursor.fetchone():
                return create_error_response(
                    ConflictError(
                        f"Memory with key '{memory_create.context_key}' already exists",
                        details={"context_key": memory_create.context_key}
                    ),
                    include_traceback=False
                )
            
            current_time = datetime.datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO project_context (context_key, value, last_updated, updated_by, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                memory_create.context_key,
                json.dumps(memory_create.context_value),
                current_time,
                requesting_admin_id,
                memory_create.description
            ))
            
            log_agent_action_to_db(cursor, requesting_admin_id, "created_memory", details={"context_key": memory_create.context_key})
            conn.commit()
            
            return JSONResponse({
                "success": True,
                "message": f"Memory '{memory_create.context_key}' created successfully"
            })
        
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except ConflictError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "create_memory"}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def update_memory_api_route(request: Request) -> JSONResponse:
    """Update an existing memory entry"""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'PUT':
        return create_error_response(
            ValidationError("Method not allowed. Use PUT for this endpoint."),
            include_traceback=False
        )
    
    path_parts = request.url.path.split('/')
    if len(path_parts) < 4 or not path_parts[-1]:
        return create_error_response(
            handle_validation_error("context_key", None, "context_key is required in URL path"),
            include_traceback=False
        )
    
    context_key = path_parts[-1]
    
    try:
        data = await get_sanitized_json_body(request)
        admin_token = data.get('token')
        
        if not verify_token(admin_token, required_role='admin'):
            return create_error_response(
                AuthenticationError("Invalid admin token"),
                include_traceback=False
            )
        
        memory_data = {k: v for k, v in data.items() if k != 'token'}
        try:
            memory_update = MemoryUpdate(**memory_data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", memory_data, str(e)),
                include_traceback=False
            )
        
        requesting_admin_id = auth_get_agent_id(admin_token)
        
        with db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT context_key FROM project_context WHERE context_key = %s", (context_key,))
            if not cursor.fetchone():
                return create_error_response(
                    NotFoundError(f"Memory '{context_key}' not found", details={"context_key": context_key}),
                    include_traceback=False
                )
            
            current_time = datetime.datetime.now().isoformat()
            
            update_fields = ["last_updated = %s", "updated_by = %s"]
            params = [current_time, requesting_admin_id]
            
            if memory_update.context_value is not None:
                update_fields.append("value = %s")
                params.append(json.dumps(memory_update.context_value))
            
            if memory_update.description is not None:
                update_fields.append("description = %s")
                params.append(memory_update.description)
            
            params.append(context_key)
            
            query = f"UPDATE project_context SET {', '.join(update_fields)} WHERE context_key = %s"
            cursor.execute(query, params)
            
            log_agent_action_to_db(cursor, requesting_admin_id, "updated_memory", details={"context_key": context_key})
            conn.commit()
            
            return JSONResponse({
                "success": True,
                "message": f"Memory '{context_key}' updated successfully"
            })
        
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except NotFoundError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "update_memory", "context_key": context_key}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def delete_memory_api_route(request: Request) -> JSONResponse:
    """Delete a memory entry"""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'DELETE':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    path_parts = request.url.path.split('/')
    if len(path_parts) < 4 or not path_parts[-1]:
        return JSONResponse({"error": "context_key is required in URL"}, status_code=400)
    
    context_key = path_parts[-1]
    
    try:
        data = await get_sanitized_json_body(request)
        admin_token = data.get('token')
        
        if not verify_token(admin_token, required_role='admin'):
            return JSONResponse({"error": "Invalid admin token"}, status_code=403)
        
        requesting_admin_id = auth_get_agent_id(admin_token)
        
        with db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT context_key FROM project_context WHERE context_key = %s", (context_key,))
            if not cursor.fetchone():
                return JSONResponse({"error": "Memory not found"}, status_code=404)
            
            cursor.execute("DELETE FROM project_context WHERE context_key = %s", (context_key,))
            
            log_agent_action_to_db(cursor, requesting_admin_id, "deleted_memory", details={"context_key": context_key})
            conn.commit()
            
            return JSONResponse({
                "success": True,
                "message": f"Memory '{context_key}' deleted successfully"
            })
        
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.error(f"Error deleting memory: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to delete memory: {str(e)}"}, status_code=500)


async def context_data_api_route(request: Request) -> JSONResponse:
    """Get only context data"""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM project_context ORDER BY last_updated DESC")
            context_data = [dict(row) for row in cursor.fetchall()]
            
            return JSONResponse(
                context_data,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
        
    except Exception as e:
        logger.error(f"Error fetching context data: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to fetch context data: {str(e)}"}, status_code=500)


# Route definitions
routes = [
    Route('/api/memories', endpoint=create_memory_api_route, name="create_memory_api", methods=['POST', 'OPTIONS']),
    Route('/api/memories/{context_key}', endpoint=update_memory_api_route, name="update_memory_api", methods=['PUT', 'OPTIONS']),
    Route('/api/memories/{context_key}', endpoint=delete_memory_api_route, name="delete_memory_api", methods=['DELETE', 'OPTIONS']),
    Route('/api/context-data', endpoint=context_data_api_route, name="context_data_api", methods=['GET', 'OPTIONS']),
    Route('/api/create-sample-memories', endpoint=create_sample_memories_route, name="create_sample_memories", methods=['POST', 'OPTIONS']),
]

