# Agent-MCP/mcp_template/mcp_server_src/db/actions/agent_db.py
import psycopg2
import json
from typing import Optional, Dict, List, Any
import datetime # Added because it's used in update_agent_db_field

from ...core.config import logger
from ..connection_factory import get_db_connection, db_connection
from ..postgres_connection import return_connection

# This module provides reusable database operations specifically for the 'agents' table.

def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single agent's details from the database by agent_id.
    Returns None if the agent is not found.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE agent_id = %s", (agent_id,))
            row = cursor.fetchone()
            if row:
                agent_data = dict(row)
                # Parse JSON fields if necessary (e.g., capabilities)
                if 'capabilities' in agent_data and isinstance(agent_data['capabilities'], str):
                    try:
                        agent_data['capabilities'] = json.loads(agent_data['capabilities'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse capabilities JSON for agent {agent_id}. Raw: {agent_data['capabilities']}")
                        agent_data['capabilities'] = [] # Default to empty list on parse error
                return agent_data
            return None
    except psycopg2.Error as e:
        logger.error(f"Database error fetching agent by ID '{agent_id}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching agent by ID '{agent_id}': {e}", exc_info=True)
        return None

def get_agent_by_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single agent's details from the database by their token.
    Returns None if the agent is not found.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE token = %s", (token,))
            row = cursor.fetchone()
            if row:
                agent_data = dict(row)
                if 'capabilities' in agent_data and isinstance(agent_data['capabilities'], str):
                    try:
                        agent_data['capabilities'] = json.loads(agent_data['capabilities'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse capabilities JSON for agent with token. Raw: {agent_data['capabilities']}")
                        agent_data['capabilities'] = []
                return agent_data
            return None
    except psycopg2.Error as e:
        logger.error(f"Database error fetching agent by token: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching agent by token: {e}", exc_info=True)
        return None

def get_all_active_agents_from_db() -> List[Dict[str, Any]]:
    """
    Fetches all agents from the database that are not 'terminated'.
    This is used for populating g.active_agents at startup.
    """
    agents_list: List[Dict[str, Any]] = []
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            # Query matches the one in server_lifecycle.application_startup
            cursor.execute("""
                SELECT token, agent_id, capabilities, created_at, status, current_task, working_directory, color 
                FROM agents WHERE status != %s
            """, ("terminated",))
            for row in cursor.fetchall():
                agent_data = dict(row)
                if 'capabilities' in agent_data and isinstance(agent_data['capabilities'], str):
                    try:
                        agent_data['capabilities'] = json.loads(agent_data['capabilities'] or '[]')
                    except json.JSONDecodeError:
                        agent_data['capabilities'] = []
                agents_list.append(agent_data)
            return agents_list
    except psycopg2.Error as e:
        logger.error(f"Database error fetching all active agents: {e}", exc_info=True)
        return [] # Return empty list on error
    except Exception as e:
        logger.error(f"Unexpected error fetching all active agents: {e}", exc_info=True)
        return []

def update_agent_db_field(agent_id: str, field_name: str, new_value: Any) -> bool:
    """
    Updates a specific field for an agent in the database.
    Handles JSON serialization for fields like 'capabilities'.
    Returns True on success, False on failure.
    """
    if field_name not in ['status', 'current_task', 'working_directory', 'color', 'capabilities', 'updated_at']:
        logger.error(f"Attempted to update an invalid or unsupported agent field: {field_name}")
        return False

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            value_to_set = new_value
            if field_name == 'capabilities':
                value_to_set = json.dumps(new_value or [])
            elif field_name == 'updated_at' and new_value is None: # Auto-set updated_at if not provided
                # PostgreSQL handles timestamps natively
                value_to_set = None  # Will use CURRENT_TIMESTAMP in SQL
            
            # Always update 'updated_at' timestamp
            # Use safe field mapping to prevent SQL injection
            allowed_fields = {
                'status': 'status',
                'current_task': 'current_task', 
                'working_directory': 'working_directory',
                'color': 'color',
                'capabilities': 'capabilities',
                'updated_at': 'updated_at'
            }
            safe_field_name = allowed_fields[field_name]  # This will raise KeyError if invalid
            
            if field_name == 'updated_at' and new_value is None:
                sql = f"UPDATE agents SET {safe_field_name} = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE agent_id = %s"
                cursor.execute(sql, (agent_id,))
            else:
                sql = f"UPDATE agents SET {safe_field_name} = %s, updated_at = CURRENT_TIMESTAMP WHERE agent_id = %s"
                cursor.execute(sql, (value_to_set, agent_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Agent '{agent_id}' field '{field_name}' updated in DB.")
                return True
            else:
                logger.warning(f"Agent '{agent_id}' not found or field '{field_name}' update had no effect in DB.")
                return False
                
    except psycopg2.Error as e:
        logger.error(f"Database error updating agent '{agent_id}' field '{field_name}': {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating agent '{agent_id}' field '{field_name}': {e}", exc_info=True)
        return False
