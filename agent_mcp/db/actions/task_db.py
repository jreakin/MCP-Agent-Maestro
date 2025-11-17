# Agent-MCP/mcp_template/mcp_server_src/db/actions/task_db.py
import psycopg2
import json
import datetime
from typing import Optional, Dict, List, Any

from ...core.config import logger
from ..connection_factory import get_db_connection, db_connection
from ..postgres_connection import return_connection

# Import WebSocket manager for real-time updates
try:
    from ...app.websocket import ws_manager
    WS_AVAILABLE = True
except ImportError:
    # WebSocket manager not available (e.g., during testing)
    WS_AVAILABLE = False
    ws_manager = None

def _broadcast_task_update(task_id: str, changes: Dict[str, Any]):
    """Helper to broadcast task updates via WebSocket (non-blocking)."""
    if not WS_AVAILABLE or not ws_manager:
        return
    
    try:
        import asyncio
        message = {
            "type": "task_update",
            "task_id": task_id,
            "changes": changes,
            "timestamp": datetime.datetime.now().isoformat()
        }
        # Try to get running event loop
        try:
            loop = asyncio.get_running_loop()
            # Schedule broadcast in background
            loop.create_task(ws_manager.broadcast("tasks", message))
        except RuntimeError:
            # No running loop, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast("tasks", message))
            loop.close()
    except Exception as e:
        logger.warning(f"Failed to broadcast task update via WebSocket: {e}")

# This module provides reusable database operations specifically for the 'tasks' table.

def _parse_task_json_fields(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to parse JSON string fields in a task dictionary."""
    if not task_data:
        return {}
    
    parsed_data = task_data.copy()
    for field_key in ["child_tasks", "depends_on_tasks", "notes"]:
        if field_key in parsed_data and isinstance(parsed_data[field_key], str):
            try:
                parsed_data[field_key] = json.loads(parsed_data[field_key] or "[]")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON for field '{field_key}' in task '{parsed_data.get('task_id', 'Unknown')}'. Raw: {parsed_data[field_key]}")
                parsed_data[field_key] = [] # Default to empty list on parse error
    return parsed_data

def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single task's details from the database by task_id.
    Parses JSON fields (child_tasks, depends_on_tasks, notes) into Python lists.
    Returns None if the task is not found.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id,))
            row = cursor.fetchone()
            if row:
                return _parse_task_json_fields(dict(row))
            return None
    except psycopg2.Error as e:
        logger.error(f"Database error fetching task by ID '{task_id}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching task by ID '{task_id}': {e}", exc_info=True)
        return None

def get_all_tasks_from_db() -> List[Dict[str, Any]]:
    """
    Fetches all tasks from the database.
    Parses JSON fields for each task.
    This is used for populating g.tasks at startup and for dashboard views.
    """
    tasks_list: List[Dict[str, Any]] = []
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            # Query matches the one in server_lifecycle.application_startup and all_tasks_api_route
            cursor.execute("SELECT * FROM tasks ORDER BY display_order ASC, created_at DESC") # Order for consistency
            for row in cursor.fetchall():
                tasks_list.append(_parse_task_json_fields(dict(row)))
            return tasks_list
    except psycopg2.Error as e:
        logger.error(f"Database error fetching all tasks: {e}", exc_info=True)
        return [] # Return empty list on error
    except Exception as e:
        logger.error(f"Unexpected error fetching all tasks: {e}", exc_info=True)
        return []

def reorder_tasks(task_ids: List[str]) -> bool:
    """
    Reorder tasks by updating their display_order field.
    The order in the task_ids list determines the new order.
    
    Args:
        task_ids: List of task IDs in the desired order
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            # Update display_order for each task based on its position in the list
            for index, task_id in enumerate(task_ids):
                cursor.execute(
                    "UPDATE tasks SET display_order = %s, updated_at = CURRENT_TIMESTAMP WHERE task_id = %s",
                    (index, task_id)
                )
            conn.commit()
            logger.info(f"Reordered {len(task_ids)} tasks")
            return True
    except psycopg2.Error as e:
        logger.error(f"Database error reordering tasks: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error reordering tasks: {e}", exc_info=True)
        return False


def get_tasks_by_agent_id(agent_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches tasks assigned to a specific agent, optionally filtered by status.
    Parses JSON fields for each task.
    """
    tasks_list: List[Dict[str, Any]] = []
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks WHERE assigned_to = %s"
            params: List[Any] = [agent_id]
            
            if status_filter:
                query += " AND status = %s"
                params.append(status_filter)
            
            query += " ORDER BY display_order ASC, created_at DESC"
            
            cursor.execute(query, tuple(params))
            for row in cursor.fetchall():
                tasks_list.append(_parse_task_json_fields(dict(row)))
            return tasks_list
    except psycopg2.Error as e:
        logger.error(f"Database error fetching tasks for agent '{agent_id}': {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching tasks for agent '{agent_id}': {e}", exc_info=True)
        return []

def update_task_fields_in_db(task_id: str, fields_to_update: Dict[str, Any]) -> bool:
    """
    Updates specified fields for a task in the database.
    Automatically updates the 'updated_at' timestamp.
    Handles JSON serialization for complex fields like 'notes', 'child_tasks', 'depends_on_tasks'.
    Returns True on success, False on failure.
    """
    if not task_id or not fields_to_update:
        logger.warning("update_task_fields_in_db called with no task_id or no fields to update.")
        return False

    try:
        with db_connection() as conn:
            cursor = conn.cursor()

            update_clauses: List[str] = []
            update_values: List[Any] = []

            for field, value in fields_to_update.items():
                # Basic validation against known task fields from postgres_schema.py
                # This list should match columns in the 'tasks' table.
                valid_fields = [
                    "title", "description", "assigned_to", "status", "priority",
                    "parent_task", "child_tasks", "depends_on_tasks", "notes", "display_order"
                ]
                if field not in valid_fields:
                    logger.warning(f"Attempted to update invalid task field: {field} for task {task_id}. Skipping.")
                    continue

                # Safe field mapping to prevent SQL injection
                safe_field_mapping = {
                    "title": "title",
                    "description": "description", 
                    "assigned_to": "assigned_to",
                    "status": "status",
                    "priority": "priority",
                    "parent_task": "parent_task",
                    "child_tasks": "child_tasks",
                    "depends_on_tasks": "depends_on_tasks",
                    "notes": "notes",
                    "display_order": "display_order"
                }
                safe_field = safe_field_mapping[field]  # This will raise KeyError if invalid
                update_clauses.append(f"{safe_field} = %s")
                if field in ["child_tasks", "depends_on_tasks", "notes"]:
                    update_values.append(json.dumps(value or [])) # Ensure JSON list for these
                else:
                    update_values.append(value)
            
            if not update_clauses:
                logger.info(f"No valid fields to update for task {task_id}.")
                return False # Or True, as no actual update was needed/performed

            # Always update the 'updated_at' timestamp
            update_clauses.append("updated_at = CURRENT_TIMESTAMP")
            # PostgreSQL handles timestamps natively, no need to append value

            update_values.append(task_id) # For the WHERE clause

            sql = f"UPDATE tasks SET {', '.join(update_clauses)} WHERE task_id = %s"
            
            cursor.execute(sql, tuple(update_values))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Task '{task_id}' updated in DB with fields: {list(fields_to_update.keys())}.")
                # Broadcast WebSocket update (non-blocking)
                _broadcast_task_update(task_id, fields_to_update)
                return True
            else:
                logger.warning(f"Task '{task_id}' not found or update had no effect in DB.")
                return False # Task might not exist or values were the same

    except psycopg2.Error as e:
        logger.error(f"Database error updating task '{task_id}': {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating task '{task_id}': {e}", exc_info=True)
        return False


def create_task_in_db(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    status: str = "pending",
    assigned_to: Optional[str] = None,
    created_by: str = "admin",
    parent_task: Optional[str] = None,
    depends_on_tasks: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    due_date: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Create a new task in the database.
    
    Args:
        title: Task title
        description: Task description
        priority: Task priority (low, medium, high, critical)
        status: Task status (pending, in_progress, completed, etc.)
        assigned_to: Agent ID assigned to task
        created_by: Agent ID that created the task
        parent_task: Parent task ID
        depends_on_tasks: List of task IDs this task depends on
        tags: List of tags
        due_date: Due date ISO string
        metadata: Additional metadata dictionary
        
    Returns:
        Task ID if successful, None otherwise
    """
    import secrets
    
    if not title:
        logger.warning("create_task_in_db called with empty title")
        return None
    
    # PostgreSQL doesn't allow null characters in strings - filter them out
    title = title.replace('\x00', '')
    if parent_task:
        parent_task = parent_task.replace('\x00', '') if parent_task else None
    if assigned_to:
        assigned_to = assigned_to.replace('\x00', '') if assigned_to else None
    if created_by:
        created_by = created_by.replace('\x00', '') if created_by else None
    
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate task ID
            task_id = f"task_{secrets.token_hex(6)}"
            created_at = datetime.datetime.now().isoformat()
            
            # Prepare task data
            task_data = {
                "task_id": task_id,
                "title": title,
                "description": description or "",
                "assigned_to": assigned_to,
                "created_by": created_by,
                "status": status,
                "priority": priority,
                "created_at": created_at,
                "updated_at": created_at,
                "parent_task": parent_task,
                "child_tasks": json.dumps([]),
                "depends_on_tasks": json.dumps(depends_on_tasks or []),
                "notes": json.dumps([]),
            }
            
            # Check which columns exist in the database
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tasks'
            """)
            existing_columns = {row['column_name'] for row in cursor.fetchall()}
            
            # Only add optional fields if columns exist in schema
            # Note: PostgreSQL schema may not have tags, metadata, due_date columns
            if tags is not None and "tags" in existing_columns:
                task_data["tags"] = json.dumps(tags)
            if due_date is not None and "due_date" in existing_columns:
                task_data["due_date"] = due_date
            if metadata is not None and "metadata" in existing_columns:
                task_data["metadata"] = json.dumps(metadata)
            
            # Build INSERT query - use parameterized query for PostgreSQL
            # Only include columns that exist in the database
            columns = [col for col in task_data.keys() if col in existing_columns]
            if not columns:
                logger.error("No valid columns found for task insert")
                return None
            
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            values = [task_data[col] for col in columns]
            
            cursor.execute(
                f"""
                INSERT INTO tasks ({columns_str})
                VALUES ({placeholders})
                """,
                values
            )
            
            # Update parent task's child_tasks if parent exists
            if parent_task and parent_task.strip() and '\x00' not in parent_task:
                try:
                    cursor.execute("SELECT child_tasks FROM tasks WHERE task_id = %s", (parent_task,))
                    parent_row = cursor.fetchone()
                    if parent_row:
                        child_tasks_json = parent_row.get("child_tasks") or "[]"
                        child_tasks = json.loads(child_tasks_json) if isinstance(child_tasks_json, str) else child_tasks_json
                        if not isinstance(child_tasks, list):
                            child_tasks = []
                        if task_id not in child_tasks:
                            child_tasks.append(task_id)
                            cursor.execute(
                                "UPDATE tasks SET child_tasks = %s, updated_at = CURRENT_TIMESTAMP WHERE task_id = %s",
                                (json.dumps(child_tasks), parent_task)
                            )
                except Exception as e:
                    logger.warning(f"Failed to update parent task {parent_task}: {e}")
            
            conn.commit()
            logger.info(f"Task '{task_id}' created in DB: '{title}'")
            return task_id
        
    except psycopg2.Error as e:
        logger.error(f"Database error creating task: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating task: {e}", exc_info=True)
        return None
