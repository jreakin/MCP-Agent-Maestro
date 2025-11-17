"""Dashboard API endpoints."""
import datetime
import json
from typing import List, Dict, Any

from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...core.config import logger
from ...core import globals as g
from ...core.auth import verify_token, get_agent_id as auth_get_agent_id
from ...utils.json_utils import get_sanitized_json_body
from ...utils.error_handlers import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    create_error_response,
    log_error,
    handle_database_error,
    handle_validation_error,
)
from ...db import db_connection
from ...db.actions.agent_actions_db import log_agent_action_to_db
from ...features.dashboard.api import (
    fetch_graph_data_logic,
    fetch_task_tree_data_logic
)
from ...features.dashboard.styles import get_node_style
from ..decorators import api_route
from ..responses import success_response
from .base import handle_options
from ...tools.admin_tools import (
    create_agent_tool_impl,
    terminate_agent_tool_impl
)
import mcp.types as mcp_types


def serialize_datetime(obj: Any) -> Any:
    """Convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj


@api_route()
async def simple_status_api_route(request: Request) -> JSONResponse:
    """Get simple system status."""
    from ...db.actions.agent_db import get_all_active_agents_from_db
    from ...db.actions.task_db import get_all_tasks_from_db
    
    agents = get_all_active_agents_from_db()
    tasks = get_all_tasks_from_db()
    
    pending_tasks = len([t for t in tasks if t.get('status') == 'pending'])
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    
    return success_response({
        "server_running": True,
        "total_agents": len(agents),
        "active_agents": len([a for a in agents if a.get('status') == 'active']),
        "total_tasks": len(tasks),
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "last_updated": datetime.datetime.now().isoformat()
    })


@api_route()
async def graph_data_api_route(request: Request) -> JSONResponse:
    """Get graph data for visualization."""
    data = await fetch_graph_data_logic(g.file_map.copy())
    return success_response(data)


@api_route()
async def task_tree_data_api_route(request: Request) -> JSONResponse:
    """Get task tree data for visualization."""
    data = await fetch_task_tree_data_logic()
    return success_response(data)


async def node_details_api_route(request: Request) -> JSONResponse:
    node_id = request.query_params.get('node_id')
    if not node_id:
        return JSONResponse({'error': 'Missing node_id parameter'}, status_code=400)
    details: Dict[str, Any] = {'id': node_id, 'type': 'unknown', 'data': {}, 'actions': [], 'related': {}}
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            parts = node_id.split('_', 1)
            node_type_from_id = parts[0] if len(parts) > 1 else node_id
            actual_id_from_node = parts[1] if len(parts) > 1 else (node_id if node_type_from_id != 'admin' else 'admin')
            details['type'] = node_type_from_id
            if node_type_from_id == 'agent':
                cursor.execute("SELECT * FROM agents WHERE agent_id = %s", (actual_id_from_node,))
                row = cursor.fetchone()
                if row: details['data'] = serialize_datetime(dict(row))
                cursor.execute("SELECT timestamp, action_type, task_id, details FROM agent_actions WHERE agent_id = %s ORDER BY timestamp DESC LIMIT 10", (actual_id_from_node,))
                details['actions'] = [serialize_datetime(dict(r)) for r in cursor.fetchall()]
                cursor.execute("SELECT task_id, title, status, priority FROM tasks WHERE assigned_to = %s ORDER BY created_at DESC LIMIT 10", (actual_id_from_node,))
                details['related']['assigned_tasks'] = [serialize_datetime(dict(r)) for r in cursor.fetchall()]
            elif node_type_from_id == 'task':
                cursor.execute("SELECT * FROM tasks WHERE task_id = %s", (actual_id_from_node,))
                row = cursor.fetchone()
                if row: details['data'] = serialize_datetime(dict(row))
                cursor.execute("SELECT timestamp, agent_id, action_type, details FROM agent_actions WHERE task_id = %s ORDER BY timestamp DESC LIMIT 10", (actual_id_from_node,))
                details['actions'] = [serialize_datetime(dict(r)) for r in cursor.fetchall()]
            elif node_type_from_id == 'context':
                cursor.execute("SELECT * FROM project_context WHERE context_key = %s", (actual_id_from_node,))
                row = cursor.fetchone()
                if row: details['data'] = dict(row)
                cursor.execute("SELECT timestamp, agent_id, action_type FROM agent_actions WHERE (action_type = 'updated_context' OR action_type = 'update_project_context') AND details LIKE %s ORDER BY timestamp DESC LIMIT 5", (f'%"{actual_id_from_node}"%',))
                details['actions'] = [dict(r) for r in cursor.fetchall()]
            elif node_type_from_id == 'file':
                details['data'] = {'filepath': actual_id_from_node, 'info': g.file_map.get(actual_id_from_node, {})}
                cursor.execute("SELECT timestamp, agent_id, action_type, details FROM agent_actions WHERE (action_type LIKE '%_file' OR action_type LIKE 'claim_file_%' OR action_type = 'release_file') AND details LIKE %s ORDER BY timestamp DESC LIMIT 5", (f'%"{actual_id_from_node}"%',))
                details['actions'] = [dict(r) for r in cursor.fetchall()]
            elif node_type_from_id == 'admin':
                details['data'] = {'name': 'Admin User / System'}
                cursor.execute("SELECT timestamp, action_type, task_id, details FROM agent_actions WHERE agent_id = 'admin' ORDER BY timestamp DESC LIMIT 10")
                details['actions'] = [dict(r) for r in cursor.fetchall()]
            if not details.get('data') and node_type_from_id not in ['admin']:
                 return JSONResponse({'error': 'Node data not found or type unrecognized'}, status_code=404)
    except Exception as e:
        logger.error(f"Error fetching details for node {node_id}: {e}", exc_info=True)
        return JSONResponse({'error': f'Failed to fetch node details: {str(e)}'}, status_code=500)
    return JSONResponse(details)


async def agents_list_api_route(request: Request) -> JSONResponse:
    agents_list_data: List[Dict[str, Any]] = []
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            admin_style = get_node_style('admin')
            agents_list_data.append({
                'agent_id': 'Admin', 'status': 'system', 'color': admin_style.get('color', '#607D8B'),
                'created_at': 'N/A', 'current_task': 'N/A'
            })
            cursor.execute("SELECT agent_id, status, color, created_at, current_task FROM agents ORDER BY created_at DESC")
            for row in cursor.fetchall(): 
                agent_dict = serialize_datetime(dict(row))
                agents_list_data.append(agent_dict)
    except Exception as e:
        logger.error(f"Error fetching agents list: {e}", exc_info=True)
        return JSONResponse({'error': f'Failed to fetch agents list: {str(e)}'}, status_code=500)
    return JSONResponse(agents_list_data)


async def tokens_api_route(request: Request) -> JSONResponse:
    try:
        agent_tokens_list = []
        for token, data in g.active_agents.items():
            if data.get("status") != "terminated":
                agent_tokens_list.append({"agent_id": data.get("agent_id"), "token": token})
        return JSONResponse({"admin_token": g.admin_token, "agent_tokens": agent_tokens_list})
    except Exception as e:
        logger.error(f"Error retrieving tokens for dashboard: {e}", exc_info=True)
        return JSONResponse({"error": f"Error retrieving tokens: {str(e)}"}, status_code=500)


async def all_tasks_api_route(request: Request) -> JSONResponse:
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            tasks_data = [serialize_datetime(dict(row)) for row in cursor.fetchall()]
            return JSONResponse(tasks_data)
    except Exception as e:
        log_error(e, context={"operation": "fetch_all_tasks"}, request=request)
        return create_error_response(
            handle_database_error(e, "fetch_all_tasks"),
            include_traceback=False
        )


async def update_task_details_api_route(request: Request) -> JSONResponse:
    if request.method != 'POST':
        return create_error_response(
            ValidationError("Method not allowed. Use POST for this endpoint."),
            include_traceback=False
        )
    try:
        import json
        data = await get_sanitized_json_body(request)
        admin_auth_token = data.get('token')
        task_id_to_update = data.get('task_id')
        new_status = data.get('status')
        if not task_id_to_update or not new_status:
            return create_error_response(
                handle_validation_error("task_id/status", None, "task_id and status are required fields."),
                include_traceback=False
            )
        if not verify_token(admin_auth_token, required_role='admin'):
            return create_error_response(
                AuthenticationError("Invalid admin token"),
                include_traceback=False
            )
        requesting_admin_id = auth_get_agent_id(admin_auth_token)
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT notes FROM tasks WHERE task_id = %s", (task_id_to_update,))
            task_row = cursor.fetchone()
            if not task_row:
                return create_error_response(
                    NotFoundError(f"Task '{task_id_to_update}' not found", details={"task_id": task_id_to_update}),
                    include_traceback=False
                )
            existing_notes_str = task_row["notes"]
            update_fields: List[str] = []
            params: List[Any] = []
            log_details: Dict[str, Any] = {"status_updated_to": new_status}
            update_fields.append("status = %s")
            params.append(new_status)
            update_fields.append("updated_at = %s")
            params.append(datetime.datetime.now().isoformat())
            if 'title' in data and data['title'] is not None:
                update_fields.append("title = %s")
                params.append(data['title'])
                log_details["title_changed"] = True
            if 'description' in data and data['description'] is not None:
                update_fields.append("description = %s")
                params.append(data['description'])
                log_details["description_changed"] = True
            if 'priority' in data and data['priority']:
                update_fields.append("priority = %s")
                params.append(data['priority'])
                log_details["priority_changed"] = True
            if 'notes' in data and data['notes'] and isinstance(data['notes'], str) and data['notes'].strip():
                try:
                    current_notes_list = json.loads(existing_notes_str or "[]")
                except json.JSONDecodeError:
                    current_notes_list = []
                new_note_entry = {"timestamp": datetime.datetime.now().isoformat(), "author": requesting_admin_id, "content": data['notes'].strip()}
                current_notes_list.append(new_note_entry)
                update_fields.append("notes = %s")
                params.append(json.dumps(current_notes_list))
                log_details["notes_added"] = True
            params.append(task_id_to_update)
            if update_fields:
                placeholders = ', '.join(update_fields)
                query = f"UPDATE tasks SET {placeholders} WHERE task_id = %s"
                cursor.execute(query, tuple(params))
            log_agent_action_to_db(cursor, requesting_admin_id, "updated_task_dashboard", task_id=task_id_to_update, details=log_details)
            conn.commit()
            if task_id_to_update in g.tasks:
                cursor.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id_to_update,))
                updated_task_for_cache = cursor.fetchone()
                if updated_task_for_cache:
                    g.tasks[task_id_to_update] = dict(updated_task_for_cache)
                    for field_key in ["child_tasks", "depends_on_tasks", "notes"]:
                        if isinstance(g.tasks[task_id_to_update].get(field_key), str):
                            try:
                                g.tasks[task_id_to_update][field_key] = json.loads(g.tasks[task_id_to_update][field_key] or "[]")
                            except json.JSONDecodeError:
                                g.tasks[task_id_to_update][field_key] = []
                else:
                    del g.tasks[task_id_to_update]
        return JSONResponse({"success": True, "message": "Task updated successfully via dashboard."})
    except ValueError as e_val:
        return create_error_response(
            handle_validation_error("request_data", None, str(e_val)),
            include_traceback=False
        )
    except Exception as e:
        log_error(e, context={"operation": "update_task", "task_id": task_id_to_update}, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


async def create_agent_dashboard_api_route(request: Request) -> JSONResponse:
    """Dashboard API endpoint to create an agent. Calls the admin tool internally."""
    if request.method != 'POST':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    try:
        data = await get_sanitized_json_body(request)
        admin_auth_token = data.get("token")
        agent_id = data.get("agent_id")
        capabilities = data.get("capabilities", [])
        working_directory = data.get("working_directory")

        if not verify_token(admin_auth_token, "admin"):
            return JSONResponse({"message": "Unauthorized: Invalid admin token for API call"}, status_code=401)

        if not agent_id:
            return JSONResponse({"message": "Agent ID is required"}, status_code=400)

        tool_args = {
            "token": admin_auth_token,
            "agent_id": agent_id,
            "capabilities": capabilities,
            "working_directory": working_directory
        }
        
        result_list: List[mcp_types.TextContent] = await create_agent_tool_impl(tool_args)
        
        if result_list and result_list[0].text.startswith(f"Agent '{agent_id}' created successfully."):
            agent_token_from_result = None
            for line in result_list[0].text.split('\n'):
                if line.startswith("Token: "):
                    agent_token_from_result = line.split("Token: ", 1)[1]
                    break
            return JSONResponse({
                "message": f"Agent '{agent_id}' created successfully via dashboard API.",
                "agent_token": agent_token_from_result
            })
        else:
            error_message = result_list[0].text if result_list else "Unknown error creating agent."
            status_code = 400
            if "Unauthorized" in error_message: status_code = 401
            if "already exists" in error_message: status_code = 409
            return JSONResponse({"message": error_message}, status_code=status_code)

    except ValueError as e_val:
        return JSONResponse({"message": str(e_val)}, status_code=400)
    except Exception as e:
        logger.error(f"Error in create_agent_dashboard_api_route: {e}", exc_info=True)
        return JSONResponse({"message": f"Error creating agent via dashboard API: {str(e)}"}, status_code=500)


async def terminate_agent_dashboard_api_route(request: Request) -> JSONResponse:
    """Dashboard API endpoint to terminate an agent. Calls the admin tool internally."""
    if request.method != 'POST':
        return JSONResponse({"error": "Method not allowed"}, status_code=405)
    try:
        data = await get_sanitized_json_body(request)
        admin_auth_token = data.get("token")
        agent_id_to_terminate = data.get("agent_id")

        if not verify_token(admin_auth_token, "admin"):
            return JSONResponse({"message": "Unauthorized: Invalid admin token for API call"}, status_code=401)

        if not agent_id_to_terminate:
            return JSONResponse({"message": "Agent ID to terminate is required"}, status_code=400)

        tool_args = {
            "token": admin_auth_token,
            "agent_id": agent_id_to_terminate
        }

        result_list: List[mcp_types.TextContent] = await terminate_agent_tool_impl(tool_args)

        if result_list and result_list[0].text.startswith(f"Agent '{agent_id_to_terminate}' terminated"):
            return JSONResponse({"message": f"Agent '{agent_id_to_terminate}' terminated successfully via dashboard API."})
        else:
            error_message = result_list[0].text if result_list else "Unknown error terminating agent."
            status_code = 400
            if "Unauthorized" in error_message: status_code = 401
            if "not found" in error_message: status_code = 404
            return JSONResponse({"message": error_message}, status_code=status_code)
            
    except ValueError as e_val:
        return JSONResponse({"message": str(e_val)}, status_code=400)
    except Exception as e:
        logger.error(f"Error in terminate_agent_dashboard_api_route: {e}", exc_info=True)
        return JSONResponse({"message": f"Error terminating agent via dashboard API: {str(e)}"}, status_code=500)


async def all_data_api_route(request: Request) -> JSONResponse:
    """Get all data in one call for caching on frontend"""
    if request.method == 'OPTIONS':
        return await handle_options(request)
    
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
            agents_data = []
            for row in cursor.fetchall():
                agent_dict = dict(row)
                agent_id = agent_dict['agent_id']
                
                agent_token = None
                for token, data in g.active_agents.items():
                    if data.get("agent_id") == agent_id and data.get("status") != "terminated":
                        agent_token = token
                        break
                
                agent_dict['auth_token'] = agent_token
                # Serialize datetime fields
                agent_dict = serialize_datetime(agent_dict)
                agents_data.append(agent_dict)
            
            agents_data.insert(0, {
                'agent_id': 'Admin',
                'status': 'system',
                'auth_token': g.admin_token,
                'created_at': 'N/A',
                'current_task': 'N/A'
            })
            
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            tasks_data = [serialize_datetime(dict(row)) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM project_context ORDER BY last_updated DESC")
            context_data = [serialize_datetime(dict(row)) for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT * FROM agent_actions 
                ORDER BY timestamp DESC 
                LIMIT 100
            """)
            actions_data = [serialize_datetime(dict(row)) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM file_metadata")
            file_metadata = [serialize_datetime(dict(row)) for row in cursor.fetchall()]
            
            response_data = {
                "agents": agents_data,
                "tasks": tasks_data,
                "context": context_data,
                "actions": actions_data,
                "file_metadata": file_metadata,
                "file_map": serialize_datetime(g.file_map),
                "admin_token": g.admin_token,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            return JSONResponse(
                response_data,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
        
    except Exception as e:
        logger.error(f"Error fetching all data: {e}", exc_info=True)
        return JSONResponse({"error": f"Failed to fetch all data: {str(e)}"}, status_code=500)


# Route definitions
routes = [
    Route('/api/all-data', endpoint=all_data_api_route, name="all_data_api", methods=['GET', 'OPTIONS']),
    Route('/api/status', endpoint=simple_status_api_route, name="simple_status_api", methods=['GET', 'OPTIONS']),
    Route('/api/graph-data', endpoint=graph_data_api_route, name="graph_data_api", methods=['GET', 'OPTIONS']),
    Route('/api/task-tree-data', endpoint=task_tree_data_api_route, name="task_tree_data_api", methods=['GET', 'OPTIONS']),
    Route('/api/node-details', endpoint=node_details_api_route, name="node_details_api", methods=['GET', 'OPTIONS']),
    Route('/api/agents', endpoint=agents_list_api_route, name="agents_list_api", methods=['GET', 'OPTIONS']),
    Route('/api/agents-list', endpoint=agents_list_api_route, name="agents_list_api_legacy", methods=['GET', 'OPTIONS']),
    Route('/api/tokens', endpoint=tokens_api_route, name="tokens_api", methods=['GET', 'OPTIONS']),
    Route('/api/tasks', endpoint=all_tasks_api_route, name="all_tasks_api", methods=['GET', 'OPTIONS']),
    Route('/api/tasks-all', endpoint=all_tasks_api_route, name="all_tasks_api_legacy", methods=['GET', 'OPTIONS']),
    Route('/api/update-task-dashboard', endpoint=update_task_details_api_route, name="update_task_dashboard_api", methods=['POST', 'OPTIONS']),
    Route('/api/create-agent', endpoint=create_agent_dashboard_api_route, name="create_agent_dashboard_api", methods=['POST', 'OPTIONS']),
    Route('/api/terminate-agent', endpoint=terminate_agent_dashboard_api_route, name="terminate_agent_dashboard_api", methods=['POST', 'OPTIONS']),
]

