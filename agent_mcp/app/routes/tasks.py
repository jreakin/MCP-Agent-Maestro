"""Enhanced task management API endpoints."""
import json

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...core.config import logger
from ...utils.json_utils import get_sanitized_json_body
from ...utils.error_handlers import (
    ValidationError,
    NotFoundError,
    DatabaseError,
    create_error_response,
    log_error,
    handle_validation_error,
)
from ...api.models import (
    TaskUpdate,
    TaskAssign,
    TaskStatusUpdate,
    TaskPriorityUpdate,
    BulkOperation,
    TaskReorder,
)
from ...db import db_connection
from .base import handle_options


async def get_task_api_route(request: Request) -> JSONResponse:
    """Get a single task by ID."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    task_id = request.path_params.get('task_id')
    if not task_id:
        return JSONResponse({"error": "task_id is required"}, status_code=400)
    
    try:
        from ...db.actions.task_db import get_task_by_id
        task = get_task_by_id(task_id)
        if not task:
            return JSONResponse({"error": "Task not found"}, status_code=404)
        return JSONResponse(task)
    except Exception as e:
        logger.error(f"Error in get_task_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to get task: {str(e)}"}, status_code=500)


async def update_task_api_route(request: Request) -> JSONResponse:
    """Update a task (full update)."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'PUT':
        return create_error_response(
            ValidationError("Method not allowed. Use PUT for this endpoint."),
            include_traceback=False
        )
    
    task_id = request.path_params.get('task_id')
    if not task_id:
        return create_error_response(
            handle_validation_error("task_id", None, "task_id is required in URL path"),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        from ...db.actions.task_db import update_task_fields_in_db, get_task_by_id
        
        try:
            task_update = TaskUpdate(**data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", data, str(e)),
                include_traceback=False
            )
        
        update_dict = task_update.model_dump(exclude_none=True)
        
        if not update_dict:
            return create_error_response(
                handle_validation_error("update_fields", None, "No fields to update"),
                include_traceback=False
            )
        
        success = update_task_fields_in_db(task_id, update_dict)
        if not success:
            return create_error_response(
                NotFoundError(f"Task '{task_id}' not found or update failed", details={"task_id": task_id}),
                include_traceback=False
            )
        
        updated_task = get_task_by_id(task_id)
        return JSONResponse(updated_task)
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "update_task", "task_id": task_id}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def delete_task_api_route(request: Request) -> JSONResponse:
    """Delete a task."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'DELETE':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    
    task_id = request.path_params.get('task_id')
    if not task_id:
        return JSONResponse({"error": "task_id is required"}, status_code=400)
    
    try:
        from ...db.actions.task_db import get_task_by_id
        from ...tools.task_tools import delete_task_tool_impl
        
        task = get_task_by_id(task_id)
        if not task:
            return JSONResponse({"error": "Task not found"}, status_code=404)
        
        result = await delete_task_tool_impl({
            'token': request.headers.get('Authorization', '').replace('Bearer ', ''),
            'task_id': task_id,
            'force_delete': True
        })
        
        if result and len(result) > 0 and hasattr(result[0], 'text'):
            if 'Error' in result[0].text:
                return JSONResponse({"error": result[0].text}, status_code=400)
        
        return JSONResponse({"success": True, "message": f"Task {task_id} deleted successfully"})
    except Exception as e:
        logger.error(f"Error in delete_task_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to delete task: {str(e)}"}, status_code=500)


async def assign_task_api_route(request: Request) -> JSONResponse:
    """Assign a task to an agent."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'POST':
        return create_error_response(
            ValidationError("Method not allowed. Use POST for this endpoint."),
            include_traceback=False
        )
    
    task_id = request.path_params.get('task_id')
    if not task_id:
        return create_error_response(
            handle_validation_error("task_id", None, "task_id is required in URL path"),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        
        try:
            assign_request = TaskAssign(**data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", data, str(e)),
                include_traceback=False
            )
        
        from ...db.actions.task_db import update_task_fields_in_db, get_task_by_id
        
        success = update_task_fields_in_db(task_id, {'assigned_to': assign_request.agent_id})
        if not success:
            return create_error_response(
                NotFoundError(f"Task '{task_id}' not found or update failed", details={"task_id": task_id}),
                include_traceback=False
            )
        
        updated_task = get_task_by_id(task_id)
        return JSONResponse(updated_task)
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "assign_task", "task_id": task_id}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def update_task_status_api_route(request: Request) -> JSONResponse:
    """Update task status."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'PUT':
        return create_error_response(
            ValidationError("Method not allowed. Use PUT for this endpoint."),
            include_traceback=False
        )
    
    task_id = request.path_params.get('task_id')
    if not task_id:
        return create_error_response(
            handle_validation_error("task_id", None, "task_id is required in URL path"),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        
        try:
            status_update = TaskStatusUpdate(**data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", data, str(e)),
                include_traceback=False
            )
        
        from ...db.actions.task_db import update_task_fields_in_db, get_task_by_id
        
        success = update_task_fields_in_db(task_id, {'status': status_update.status})
        if not success:
            return create_error_response(
                NotFoundError(f"Task '{task_id}' not found or update failed", details={"task_id": task_id}),
                include_traceback=False
            )
        
        updated_task = get_task_by_id(task_id)
        return JSONResponse(updated_task)
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "update_task_status", "task_id": task_id}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def update_task_priority_api_route(request: Request) -> JSONResponse:
    """Update task priority."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'PUT':
        return create_error_response(
            ValidationError("Method not allowed. Use PUT for this endpoint."),
            include_traceback=False
        )
    
    task_id = request.path_params.get('task_id')
    if not task_id:
        return create_error_response(
            handle_validation_error("task_id", None, "task_id is required in URL path"),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        
        try:
            priority_update = TaskPriorityUpdate(**data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", data, str(e)),
                include_traceback=False
            )
        
        from ...db.actions.task_db import update_task_fields_in_db, get_task_by_id
        
        success = update_task_fields_in_db(task_id, {'priority': priority_update.priority})
        if not success:
            return create_error_response(
                NotFoundError(f"Task '{task_id}' not found or update failed", details={"task_id": task_id}),
                include_traceback=False
            )
        
        updated_task = get_task_by_id(task_id)
        return JSONResponse(updated_task)
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "update_task_priority", "task_id": task_id}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def reorder_tasks_api_route(request: Request) -> JSONResponse:
    """Reorder tasks (for kanban/priority)."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'PUT':
        return create_error_response(
            ValidationError("Method not allowed. Use PUT for this endpoint."),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        
        try:
            reorder_data = TaskReorder(**data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", data, str(e)),
                include_traceback=False
            )
        
        from ...db.actions.task_db import reorder_tasks
        
        success = reorder_tasks(reorder_data.task_ids)
        if not success:
            return create_error_response(
                DatabaseError("Failed to reorder tasks"),
                include_traceback=False
            )
        
        return JSONResponse({
            "success": True,
            "message": f"Successfully reordered {len(reorder_data.task_ids)} tasks",
            "task_ids": reorder_data.task_ids
        })
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "reorder_tasks"}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def bulk_update_tasks_api_route(request: Request) -> JSONResponse:
    """Perform bulk operations on multiple tasks."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    if request.method != 'POST':
        return create_error_response(
            ValidationError("Method not allowed. Use POST for this endpoint."),
            include_traceback=False
        )
    
    try:
        data = await get_sanitized_json_body(request)
        from ...db.actions.task_db import update_task_fields_in_db, get_task_by_id
        
        try:
            bulk_op = BulkOperation(**data)
        except Exception as e:
            return create_error_response(
                handle_validation_error("request_data", data, str(e)),
                include_traceback=False
            )
        
        results = []
        for task_id in bulk_op.task_ids:
            try:
                if bulk_op.operation == 'update_status':
                    success = update_task_fields_in_db(task_id, {'status': bulk_op.value})
                elif bulk_op.operation == 'update_priority':
                    success = update_task_fields_in_db(task_id, {'priority': bulk_op.value})
                elif bulk_op.operation == 'assign':
                    success = update_task_fields_in_db(task_id, {'assigned_to': bulk_op.value})
                elif bulk_op.operation == 'add_tags':
                    task = get_task_by_id(task_id)
                    if task:
                        current_tags = task.get('tags', [])
                        if isinstance(current_tags, str):
                            current_tags = json.loads(current_tags) if current_tags else []
                        new_tags = list(set(current_tags + bulk_op.value))
                        success = update_task_fields_in_db(task_id, {'tags': json.dumps(new_tags)})
                    else:
                        success = False
                elif bulk_op.operation == 'delete':
                    from ...tools.task_tools import delete_task_tool_impl
                    result = await delete_task_tool_impl({
                        'token': request.headers.get('Authorization', '').replace('Bearer ', ''),
                        'task_id': task_id,
                        'force_delete': True
                    })
                    success = result and len(result) > 0 and 'Error' not in (result[0].text if hasattr(result[0], 'text') else '')
                else:
                    success = False
                
                results.append({'task_id': task_id, 'success': success})
            except Exception as e:
                logger.error(f"Error processing task {task_id} in bulk operation: {e}")
                results.append({'task_id': task_id, 'success': False, 'error': str(e)})
        
        return JSONResponse({
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'succeeded': sum(1 for r in results if r.get('success')),
                'failed': sum(1 for r in results if not r.get('success'))
            }
        })
    except ValidationError as e:
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, context={"operation": "bulk_update_tasks"}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def get_task_history_api_route(request: Request) -> JSONResponse:
    """Get task history from agent actions."""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    task_id = request.path_params.get('task_id')
    if not task_id:
        return JSONResponse({"error": "task_id is required"}, status_code=400)
    
    try:
        from ...db import db_connection
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, agent_id, action_type, details FROM agent_actions WHERE task_id = %s ORDER BY timestamp DESC LIMIT 100",
                (task_id,)
            )
            actions = [dict(row) for row in cursor.fetchall()]
            return JSONResponse({"task_id": task_id, "history": actions})
    except Exception as e:
        logger.error(f"Error in get_task_history_api_route: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to get task history: {str(e)}"}, status_code=500)


# Route definitions
routes = [
    Route('/api/tasks/{task_id}', endpoint=get_task_api_route, name="get_task_api", methods=['GET', 'OPTIONS']),
    Route('/api/tasks/{task_id}/history', endpoint=get_task_history_api_route, name="get_task_history_api", methods=['GET', 'OPTIONS']),
    Route('/api/tasks/{task_id}', endpoint=update_task_api_route, name="update_task_api", methods=['PUT', 'OPTIONS']),
    Route('/api/tasks/{task_id}', endpoint=delete_task_api_route, name="delete_task_api", methods=['DELETE', 'OPTIONS']),
    Route('/api/tasks/{task_id}/assign', endpoint=assign_task_api_route, name="assign_task_api", methods=['POST', 'OPTIONS']),
    Route('/api/tasks/{task_id}/status', endpoint=update_task_status_api_route, name="update_task_status_api", methods=['PUT', 'OPTIONS']),
    Route('/api/tasks/{task_id}/priority', endpoint=update_task_priority_api_route, name="update_task_priority_api", methods=['PUT', 'OPTIONS']),
    Route('/api/tasks/reorder', endpoint=reorder_tasks_api_route, name="reorder_tasks_api", methods=['PUT', 'OPTIONS']),
    Route('/api/tasks/bulk', endpoint=bulk_update_tasks_api_route, name="bulk_update_tasks_api", methods=['POST', 'OPTIONS']),
]

