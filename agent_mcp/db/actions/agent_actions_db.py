# Agent-MCP/mcp_template/mcp_server_src/db/actions/agent_actions_db.py
import psycopg2
import json
import datetime

# Import the central logger and database connection function
from ...core.config import logger

# Original location: main.py lines 256-263 (_log_agent_action function)
def log_agent_action_to_db(
    cursor: psycopg2.extensions.cursor,
    agent_id: str,
    action_type: str,
    task_id: str = None,
    details: dict = None
) -> None:
    """
    Internal helper to insert an entry into the agent_actions table.
    This function expects an active database cursor. The caller is responsible
    for connection management (commit/rollback, close).

    Args:
        cursor: An active psycopg2 cursor object.
        agent_id: The ID of the agent performing the action (or 'admin').
        action_type: A string describing the type of action.
        task_id: Optional ID of the task related to this action.
        details: Optional dictionary containing additional details about the action (will be JSON serialized).
    """
    # PostgreSQL handles timestamps natively, use CURRENT_TIMESTAMP
    details_json = None
    if details is not None:
        try:
            details_json = json.dumps(details)
        except TypeError as e:
            logger.error(f"Failed to serialize 'details' for agent action logging (agent: {agent_id}, action: {action_type}): {e}. Storing as string.")
            details_json = str(details) # Fallback to string representation

    try:
        # PostgreSQL uses %s placeholders and CURRENT_TIMESTAMP for timestamps
        cursor.execute("""
            INSERT INTO agent_actions (agent_id, action_type, task_id, timestamp, details)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
        """, (agent_id, action_type, task_id, details_json))
        # logger.debug(f"Logged action: {agent_id} - {action_type}") # Original main.py:263 (optional debug log)
    except psycopg2.Error as e:
        # Log error but don't crash the primary operation that called this.
        # Original main.py line 266
        logger.error(f"Failed to log agent action '{action_type}' for agent '{agent_id}' (task_id: {task_id}) to DB: {e}")
    except Exception as e: # Original main.py line 268
        logger.error(f"Unexpected error logging agent action '{action_type}' for agent '{agent_id}': {e}", exc_info=True)

# No other functions were solely dedicated to agent_actions table in the original main.py.
# If other specific queries/updates for agent_actions arise, they can be added here.
